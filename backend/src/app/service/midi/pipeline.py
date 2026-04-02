# app/service/midi/pipeline.py
"""
MIDI extraction pipeline — mirrors EffectExtractionPipeline structure.

document
  -> candidate MIDI chunks
  -> route brand (reuses same router as effects)
  -> group by page
  -> MIDI page gate (skip pages without MIDI content)
  -> brand-specific MIDI prompt (1 LLM call per page)
  -> brand-specific MIDI post-process
  -> bulk upsert to raw_midi_entries (1 DB txn per page)

No chunk refs are stored (midi_chunk_refs not implemented yet).
"""
from __future__ import annotations

import json
from collections import defaultdict
from typing import Callable, Optional, Tuple

from app.db import get_db_con
from app.service.effects.extractor_factory import EffectExtractorFactory
from app.service.effects.extract_router import EffectExtractRouter
from app.service.effects.strategies import BrandExtractStrategy, BrandMatchResult
from app.dao import midi_dao


class MidiExtractionPipeline:
    """
    Page-level MIDI extraction pipeline with brand-aware routing.
    Uses the same brand strategies as the effect pipeline but calls
    the MIDI-specific methods (should_process_midi_page, build_midi_page_prompt,
    post_process_midi).
    """

    def __init__(
        self,
        extractor_kind: str = "llm",
        confidence_threshold: float = 0.6,
        extractor_kwargs: dict | None = None,
    ):
        extractor_kwargs = extractor_kwargs or {}
        self.extractor = EffectExtractorFactory.create(extractor_kind, **extractor_kwargs)
        self.confidence_threshold = float(confidence_threshold)
        self.device_name = extractor_kwargs.get("device_name", "")
        self.brand_hint  = extractor_kwargs.get("brand", "")

        self._router = EffectExtractRouter()
        self._strategy: Optional[BrandExtractStrategy] = None
        self._match_result: Optional[BrandMatchResult] = None

    def run(
        self,
        document_id: str,
        on_chunk_done: Optional[Callable[[dict, bool, Optional[Exception]], None]] = None,
    ) -> Tuple[int, int]:
        """
        Returns: (total_midi_saved, processed_pages)
        """
        print(f"[midi] pipeline.run document={document_id}")

        # 1) Fetch MIDI candidate chunks
        with get_db_con() as conn:
            chunks = midi_dao.get_candidate_midi_chunks(conn, document_id)

        if not chunks:
            print("[midi] no candidate chunks found, exiting")
            return (0, 0)

        # 2) Route to brand strategy (same router as effects pipeline)
        sample_text = " ".join(
            (c.get("content") or "")[:300] for c in chunks[:8]
        )
        self._strategy, self._match_result = self._router.route(
            device_name=self.device_name,
            brand_hint=self.brand_hint,
            sample_text=sample_text,
        )

        # 3) Guard: skip if the matched strategy does not support MIDI extraction
        if not self._strategy.supports_midi():
            print(
                f"[midi] strategy={self._match_result.brand_key} does not support MIDI "
                "extraction. Skipping."
            )
            return (0, 0)

        # 4) Group chunks by page
        pages = defaultdict(list)
        for c in chunks:
            pages[str(c.get("page") or "unknown")].append(c)

        total_saved  = 0
        total_pages  = len(pages)
        processed    = 0
        skipped      = 0

        # 5) Process each page
        for page, page_chunks in pages.items():
            ok  = True
            err: Optional[Exception] = None
            try:
                if not self._strategy.should_process_midi_page(page_chunks):
                    skipped += 1
                    print(
                        f"[midi] page={page} SKIPPED by page gate "
                        f"(strategy={self._match_result.brand_key})"
                    )
                    continue

                print(
                    f"[midi] page={page} PROCESSING "
                    f"(strategy={self._match_result.brand_key}, "
                    f"n_chunks={len(page_chunks)})"
                )
                n = self._process_page(page, page_chunks)
                total_saved += n

            except Exception as e:
                ok  = False
                err = e
                print(f"[midi] page={page} FAILED: {e}")
            finally:
                processed += 1
                if on_chunk_done:
                    try:
                        on_chunk_done(
                            {"id": f"midi_page:{page}", "page": page, "n_chunks": len(page_chunks)},
                            ok,
                            err,
                        )
                    except Exception as cb_e:
                        print(f"[midi] on_chunk_done callback error: {cb_e}")

        print(
            f"[midi] DONE: total_pages={total_pages}, "
            f"processed={processed}, skipped={skipped}, "
            f"total_saved={total_saved}, "
            f"brand={self._match_result.brand_key}"
        )
        return (total_saved, processed)

    # ------------------------------------------------------------------

    def _process_page(self, page: str, chunks: list[dict]) -> int:
        """Process one page. Returns number of MIDI entries saved."""

        # 1) Build payload with integer indices
        payload = []
        index_to_chunk_id: dict[int, str] = {}

        idx = 0
        for c in chunks:
            text = (c.get("content") or "").strip()
            if not text:
                continue
            index_to_chunk_id[idx] = str(c["id"])
            payload.append({
                "chunk_index": idx,
                "page":        c.get("page"),
                "section":     c.get("section"),
                "text":        text,
            })
            idx += 1

        if not payload:
            return 0

        valid_indices = set(index_to_chunk_id.keys())

        # 2) Brand-specific MIDI prompt
        prompt = self._strategy.build_midi_page_prompt(
            device_name=self.device_name or self._match_result.device_family,
            page_chunks_json=json.dumps(payload, ensure_ascii=False),
            page_number=page,
            allowed_indices=list(valid_indices),
        )

        # 3) Single LLM call
        data = self.extractor.extract(prompt, mode="page", output_key="midi_mappings")
        if not isinstance(data, dict):
            return 0

        entries = data.get("midi_mappings") or []
        if not isinstance(entries, list) or not entries:
            return 0

        # 4) Brand-specific MIDI post-processing
        entries = self._strategy.post_process_midi(entries)

        # 5) Filter by confidence and valid source_chunk_indices
        filtered: list[dict] = []
        for e in entries:
            if not isinstance(e, dict):
                continue

            target_name = (e.get("target_name") or "").strip()
            if not target_name:
                continue

            msg_type = (e.get("message_type") or "").upper().strip()
            if msg_type not in ("CC", "PC", "BANK"):
                continue

            try:
                conf = float(e.get("confidence", 0.0) or 0.0)
            except Exception:
                conf = 0.0
            if conf < self.confidence_threshold:
                continue

            # Grounding check: at least one source_chunk_index must be valid
            raw_indices = e.get("source_chunk_indices") or []
            if not isinstance(raw_indices, list):
                raw_indices = []

            has_valid = any(
                int(ri) in valid_indices
                for ri in raw_indices
                if isinstance(ri, (int, float, str)) and str(ri).lstrip("-").isdigit()
            )
            if not has_valid:
                continue

            filtered.append(e)

        if not filtered:
            return 0

        # 5b) MIDI value range validation — drop entries the DB CHECK would reject
        range_valid: list[dict] = []
        for e in filtered:
            target_name = (e.get("target_name") or "").strip()
            msg_type    = (e.get("message_type") or "").upper()
            drop_reason = None

            midi_channel = e.get("midi_channel")
            cc_number    = e.get("cc_number")
            pc_number    = e.get("pc_number")
            bank_msb     = e.get("bank_msb")
            bank_lsb     = e.get("bank_lsb")

            if midi_channel is not None and not (1 <= int(midi_channel) <= 16):
                drop_reason = ("midi_channel", midi_channel)
            elif msg_type == "CC" and cc_number is not None and not (0 <= int(cc_number) <= 127):
                drop_reason = ("cc_number", cc_number)
            elif pc_number is not None and not (0 <= int(pc_number) <= 127):
                drop_reason = ("pc_number", pc_number)
            elif bank_msb is not None and not (0 <= int(bank_msb) <= 127):
                drop_reason = ("bank_msb", bank_msb)
            elif bank_lsb is not None and not (0 <= int(bank_lsb) <= 127):
                drop_reason = ("bank_lsb", bank_lsb)

            if drop_reason:
                field, value = drop_reason
                print(f"[midi] dropped '{target_name}': {field}={value} out of MIDI range")
                continue

            range_valid.append(e)

        if not range_valid:
            return 0

        # 6) DB: bulk upsert + commit (no chunk refs for now)
        kb_source_id    = chunks[0]["kb_source_id"]
        device_model_id = chunks[0]["device_model_id"]
        source_section  = next((c.get("section") for c in chunks if c.get("section")), None)

        try:
            source_page = int(chunks[0].get("page")) if chunks[0].get("page") is not None else None
        except Exception:
            source_page = None

        with get_db_con() as conn:
            id_map = midi_dao.upsert_raw_midi_bulk(
                conn,
                kb_source_id=kb_source_id,
                device_model_id=device_model_id,
                entries=range_valid,
                source_page=source_page,
                source_section=source_section,
            )
            conn.commit()

        n_saved = len(id_map)
        print(f"[midi] page={page} SAVED: entries={n_saved}")
        return n_saved
