# app/service/kb_ingestion_service.py
import os
import json
from typing import Any, Dict, Optional
import time

from app.db import get_db_con
from app.dao import device_dao
from app.dao import job_dao
from app.service.doc_factory import DocProcessorFactory
from app.llm.embeddings_factory import EmbeddingsFactory, EmbeddingsConfig
from app.service.effects.pipeline import EffectExtractionPipeline
from app.service.doc_processing.strategy_router import pick_profile, should_run_effect_pipeline

from app.service.embeddings_retry import embed_documents_resilient

UPLOAD_DIR = "uploads"

# Initialize embeddings once (module-level singleton) to avoid repeated loading.
qwen_embeddings = EmbeddingsFactory.create(EmbeddingsConfig(provider="qwen"))


def _build_device_name_from_ctx(ctx: Dict[str, Any]) -> str:
    """Build a human-readable device name from job context."""
    brand = (ctx.get("brand") or "").strip()
    model = (ctx.get("model") or "").strip()
    variant = (ctx.get("variant") or "").strip()

    name = f"{brand} {model}".strip()
    if variant and variant.lower() not in model.lower():
        name = f"{name} {variant}".strip()

    return name or "Device"


def _resolve_file_path(ctx: Dict[str, Any]) -> str:
    """
    Resolve the local file path for the source document.
    Checks for 'file_path' (absolute) or 'file_name' (relative to UPLOAD_DIR).
    """
    file_path = ctx.get("file_path")
    if file_path:
        return file_path

    file_name = ctx.get("file_name")
    if not file_name:
        raise ValueError("Job context missing 'file_name' or 'file_path'.")

    return os.path.join(UPLOAD_DIR, file_name)

def _log_embed_fail(s: int, e: int, err: Exception):
    # s,e are text index range for this batch
    print(f"⚠️ embedding batch failed [{s}:{e}] err={err!r}")


def process_document_embedding_worker(job_id: str) -> None:
    """
    Background worker:
      - Updates job status through CHUNKING -> EMBEDDING -> READY
      - Parses document into chunks based on profile
      - Generates embeddings and inserts into DB
      - Triggers asynchronous effects enrichment
    """
    # 0) Load job context from DB (single source of truth)
    # time.sleep(0.5)
    try:
        with get_db_con() as conn:
            ctx: Optional[Dict[str, Any]] = job_dao.get_job_context(conn, job_id)
    except Exception as e:
        print(f"❌ Failed to load job context for job {job_id}: {e}")
        try:
            with get_db_con() as conn:
                job_dao.update_job(
                    conn, job_id,
                    status="FAILED", stage="FAILED",
                    progress=100, error=str(e),
                )
                conn.commit()
        except Exception as _e:
            print(f"⚠️ Failed to update job status after context load error: {_e}")
        return

    if not ctx:
        print(f"❌ Job context not found for job {job_id}")
        return

    # --- FIX: Extract variables BEFORE the try block so they are available in except ---
    document_id = ctx.get("document_id")
    user_id = ctx.get("user_id")
    file_path = _resolve_file_path(ctx)
    device_name = ctx.get("device_name") or _build_device_name_from_ctx(ctx)
    profile = pick_profile(ctx)
    # ----------------------------------------------------------------------------------

    try:
        # 1) Mark start: CHUNKING
        with get_db_con() as conn:
            job_dao.update_job(conn, job_id, status="RUNNING", stage="CHUNKING", progress=10)
            conn.commit()

        # 2) Chunk the document using the resolved profile
        processor = DocProcessorFactory.get_processor(file_path, profile=profile)
        chunks = processor.process_to_chunks(file_path, profile=profile)

        if not chunks:
            with get_db_con() as conn:
                job_dao.update_job(
                    conn, job_id,
                    status="FAILED", stage="FAILED",
                    progress=100, error="No chunks extracted",
                )
                conn.commit()
            return

        # 3) Mark: EMBEDDING
        with get_db_con() as conn:
            job_dao.update_job(conn, job_id, status="RUNNING", stage="EMBEDDING", progress=30)
            conn.commit()

        # 4) Embed chunk texts
        texts = [c.page_content for c in chunks]
        # vectors = qwen_embeddings.embed_documents(texts)
        vectors = embed_documents_resilient(
            qwen_embeddings,
            texts,
            batch_size=32,
            max_retries=5,  # 你想更稳就 7
            base_delay_s=1.0,
            max_delay_s=20.0,
            jitter_s=0.5,
            on_batch_error=_log_embed_fail,
        )

        # 5) Prepare batch insert payload
        chunks_data = []
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            # Convert vector list to string representation for SQL
            vector_str = "[" + ",".join(f"{float(x):.8f}" for x in vector) + "]"

            # Enrich metadata for downstream filtering/debugging
            meta = dict(chunk.metadata or {})
            meta.update({
                "device_name": device_name,
                "brand": ctx.get("brand"),
                "model": ctx.get("model"),
                "variant": ctx.get("variant"),
                "doc_type": ctx.get("doc_type"),
                "source_type": ctx.get("source_type"),
                "chunk_profile": profile.name
            })

            chunks_data.append(
                (
                    user_id,
                    document_id,
                    i,
                    chunk.page_content,
                    vector_str,
                    json.dumps(meta),
                )
            )

        # 6) Insert chunks into DB
        with get_db_con() as conn:
            device_dao.insert_document_chunks(conn, user_id, document_id, chunks_data)
            conn.commit()

        # 7) Mark READY: Core ingestion finished
        with get_db_con() as conn:
            job_dao.update_job(conn, job_id, status="READY", stage="READY", progress=100)
            conn.commit()

        print(f"✅ READY document {document_id} (job {job_id})")

        # 8) Effects enrichment: Optional step based on source_type
        print("ctx=",ctx)
        # use_effect = should_run_effect_pipeline(ctx)
        if not should_run_effect_pipeline(ctx):
            with get_db_con() as conn:
                job_dao.set_enrichment_progress(
                    conn, job_id, enrichment_status="SKIPPED", total=0, done=0
                )
                conn.commit()
            print(f"⏭️ Effect pipeline skipped for job {job_id}")
        else:
            try:
                pipeline = EffectExtractionPipeline(extractor_kwargs={"device_name": device_name})
                # pipeline = EffectExtractionPipeline(
                #     extractor_kwargs={
                #         "brand": ctx.get("brand"),
                #         "model": ctx.get("model"),
                #         "variant": ctx.get("variant"),
                #         "device_name": device_name,
                #     }
                # )

                with get_db_con() as conn:
                    job_dao.set_enrichment_progress(conn, job_id, enrichment_status="RUNNING", total=0, done=0)
                    conn.commit()

                def on_chunk_done(_chunk, ok: bool, err):
                    with get_db_con() as conn:
                        job_dao.inc_enrichment_done(conn, job_id, delta=1)
                        conn.commit()

                total_effects, processed_pages = pipeline.run(document_id, on_chunk_done=on_chunk_done)
                print(f"--- PIPELINE FINISHED ---")
                print(f"Document ID: {document_id}")
                print(f"Total Effects Saved: {total_effects}, Pages Processed: {processed_pages}")

                with get_db_con() as conn:
                    status = "DONE" if total_effects > 0 else "SKIPPED"
                    job_dao.set_enrichment_progress(conn, job_id, enrichment_status=status, total=total_effects,
                                                    done=total_effects)
                    conn.commit()

            except Exception as e:
                print(f"⚠️ Effect pipeline failed for doc {document_id}: {e}")
                # Fallback: Update enrichment status to FAILED without crashing the main job
                try:
                    with get_db_con() as conn:
                        job_dao.set_enrichment_progress(conn, job_id, enrichment_status="FAILED", total=0, done=0)
                        conn.commit()
                except Exception:
                    pass

        print(f"[debug] === REACHED STEP 9 checkpoint === job={job_id}")
        # 9) MIDI enrichment: requires BOTH supports_midi=True AND source_type="mixed"
        try:
            with get_db_con() as conn:
                _supports_midi = device_dao.get_document_device_supports_midi(conn, document_id)
        except Exception as e_midi_check:
            print(f"⚠️ Could not check supports_midi for doc {document_id}: {e_midi_check}")
            _supports_midi = False

        _source_type = (ctx.get("source_type") or "").strip().lower()
        _run_midi = _supports_midi and _source_type == "mixed"

        if _run_midi:
            try:
                from app.service.midi.pipeline import MidiExtractionPipeline

                with get_db_con() as conn:
                    job_dao.set_midi_enrichment(conn, job_id, status="RUNNING", total=0)
                    conn.commit()

                midi_pipeline = MidiExtractionPipeline(
                    extractor_kwargs={"device_name": device_name}
                )
                total_midi, midi_pages = midi_pipeline.run(document_id)
                print(
                    f"[midi] DONE document={document_id}: "
                    f"total_midi={total_midi}, pages_processed={midi_pages}"
                )

                with get_db_con() as conn:
                    job_dao.set_midi_enrichment(conn, job_id, status="DONE", total=total_midi)
                    conn.commit()

            except Exception as e_midi:
                print(f"⚠️ MIDI pipeline failed for doc {document_id}: {e_midi}")
                try:
                    with get_db_con() as conn:
                        job_dao.set_midi_enrichment(conn, job_id, status="FAILED", total=0)
                        conn.commit()
                except Exception:
                    pass
        else:
            _skip_reason = (
                f"supports_midi={_supports_midi}, source_type={_source_type!r}"
            )
            print(f"⏭️ MIDI pipeline skipped for job {job_id} ({_skip_reason})")
            try:
                with get_db_con() as conn:
                    job_dao.set_midi_enrichment(conn, job_id, status="SKIPPED", total=0)
                    conn.commit()
            except Exception:
                pass

    except Exception as e:
        # Handle main processing failures
        with get_db_con() as conn:
            job_dao.update_job(conn, job_id, status="FAILED", stage="FAILED", progress=100, error=str(e))
            conn.commit()
        # document_id is now safe to access here
        print(f"❌ Failed to process document {document_id} (job {job_id}): {e}")