# app/service/effects/pipeline.py
from __future__ import annotations

from typing import Callable, Optional, Tuple
from collections import defaultdict
import json

from app.db import get_db_con
from app.service.effects.extractor_factory import EffectExtractorFactory
from app.dao import effect_dao
from app.service.effects.extract_router import EffectExtractRouter
from app.service.effects.strategies import BrandExtractStrategy, BrandMatchResult


class EffectExtractionPipeline:
    """
    Page-level pipeline with brand-aware routing.

    document
      -> candidate chunks
      -> route brand (once per document)
      -> group by page
      -> page gate (skip non-effect pages)
      -> brand-specific prompt (1 LLM call per page, using chunk indices)
      -> brand-specific post-process
      -> map indices back to real chunk IDs
      -> bulk upsert + bulk bind (1 DB txn per page)
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
        self.brand_hint = extractor_kwargs.get("brand", "")

        self._router = EffectExtractRouter()
        self._strategy: Optional[BrandExtractStrategy] = None
        self._match_result: Optional[BrandMatchResult] = None

    def run(
        self,
        document_id: str,
        on_chunk_done: Optional[Callable[[dict, bool, Optional[Exception]], None]] = None,
    ) -> Tuple[int, int]:
        """
        Returns: (total_effects_saved, processed_pages)
        """
        print(f"[effects] pipeline.run document={document_id}")

        # 1) Fetch candidate chunks
        with get_db_con() as conn:
            chunks = effect_dao.get_candidate_chunks(conn, document_id)

        if not chunks:
            print("[effects] no candidate chunks found, exiting")
            return (0, 0)

        # 2) Route to brand strategy
        sample_text = " ".join(
            (c.get("content") or "")[:300] for c in chunks[:8]
        )
        self._strategy, self._match_result = self._router.route(
            device_name=self.device_name,
            brand_hint=self.brand_hint,
            sample_text=sample_text,
        )

        # 3) Group chunks by page
        pages = defaultdict(list)
        for c in chunks:
            pages[str(c.get("page") or "unknown")].append(c)

        total_effects = 0
        total_pages = len(pages)
        processed = 0
        skipped = 0

        # 4) Process each page
        for page, page_chunks in pages.items():
            ok = True
            err: Optional[Exception] = None
            try:
                if not self._strategy.should_process_page(page_chunks):
                    skipped += 1
                    print(f"[effects] page={page} SKIPPED by page gate "
                          f"(strategy={self._match_result.brand_key})")
                    continue

                print(f"[effects] page={page} PROCESSING "
                      f"(strategy={self._match_result.brand_key}, "
                      f"n_chunks={len(page_chunks)})")
                n = self._process_page(page, page_chunks)
                total_effects += n

            except Exception as e:
                ok = False
                err = e
                print(f"[effects] page={page} FAILED: {e}")
            finally:
                processed += 1
                if on_chunk_done:
                    try:
                        on_chunk_done(
                            {"id": f"page:{page}", "page": page, "n_chunks": len(page_chunks)},
                            ok,
                            err,
                        )
                    except Exception as cb_e:
                        print(f"[effects] on_chunk_done callback error: {cb_e}")

        print(f"[effects] DONE: total_pages={total_pages}, "
              f"processed={processed}, skipped={skipped}, "
              f"total_effects={total_effects}, "
              f"brand={self._match_result.brand_key}")
        return (total_effects, processed)

    # ------------------------------------------------------------------

    def _process_page(self, page: str, chunks: list[dict]) -> int:
        """Process one page. Returns number of effects saved."""

        # 1) Build payload with integer indices, map index -> real chunk ID
        payload = []
        index_to_chunk_id: dict[int, str] = {}

        idx = 0
        for c in chunks:
            text = (c.get("content") or "").strip()
            if not text:
                continue
            chunk_id_str = str(c["id"])
            index_to_chunk_id[idx] = chunk_id_str
            payload.append({
                "chunk_index": idx,
                "page": c.get("page"),
                "section": c.get("section"),
                "text": text,
            })
            idx += 1

        if not payload:
            return 0

        valid_indices = set(index_to_chunk_id.keys())

        # 2) Brand-specific prompt (now receives indices, not UUIDs)
        prompt = self._strategy.build_page_prompt(
            device_name=self.device_name or self._match_result.device_family,
            page_chunks_json=json.dumps(payload, ensure_ascii=False),
            page_number=page,
            allowed_indices=list(valid_indices),
        )

        # 3) Single LLM call
        data = self.extractor.extract(prompt, mode="page")
        if not isinstance(data, dict):
            return 0

        modules = data.get("modules") or []
        if not isinstance(modules, list) or not modules:
            return 0

        # 4) Brand-specific post-processing
        modules = self._strategy.post_process(modules)

        # 5) Filter, normalize, and map indices back to real chunk IDs
        filtered: list[dict] = []
        for m in modules:
            print(f"[debug] after post_process: raw_name={m.get('raw_name')}, raw_type={m.get('raw_type')}")
            if not isinstance(m, dict):
                continue

            name = (m.get("raw_name") or "").strip()
            if not name:
                continue

            try:
                conf = float(m.get("confidence", 0.0) or 0.0)
            except Exception:
                conf = 0.0
            if conf < self.confidence_threshold:
                continue

            # Map source_chunk_indices -> real chunk IDs
            raw_indices = m.get("source_chunk_indices") or []
            if not isinstance(raw_indices, list):
                raw_indices = []

            source_chunk_ids = []
            for ri in raw_indices:
                try:
                    ri_int = int(ri)
                except (ValueError, TypeError):
                    continue
                if ri_int in valid_indices:
                    source_chunk_ids.append(index_to_chunk_id[ri_int])

            if not source_chunk_ids:
                print(f"[effects] dropped '{name}': no valid source_chunk_indices")
                continue

            raw_type = (m.get("raw_type") or "UNKNOWN").strip() or "UNKNOWN"

            filtered.append({
                "raw_name": name,
                "raw_type": raw_type,
                "raw_category": m.get("raw_category"),
                "raw_description": m.get("raw_description"),
                "confidence": conf,
                "meta": m.get("meta") or {},
                "source_chunk_ids": source_chunk_ids,
            })

        if not filtered:
            return 0

        # 6) DB: bulk upsert + bulk bind + commit
        kb_source_id = chunks[0]["kb_source_id"]
        device_model_id = chunks[0]["device_model_id"]
        source_section = next((c.get("section") for c in chunks if c.get("section")), None)

        try:
            source_page = int(chunks[0].get("page")) if chunks[0].get("page") is not None else None
        except Exception:
            source_page = None

        with get_db_con() as conn:
            id_map = effect_dao.upsert_raw_effects_bulk(
                conn,
                kb_source_id=kb_source_id,
                device_model_id=device_model_id,
                effects=filtered,
                source_page=source_page,
                source_section=source_section,
            )

            pairs = []
            for m in filtered:
                rn_norm = effect_dao.normalize_raw_name(m["raw_name"])
                rt = (m.get("raw_type") or "UNKNOWN").strip() or "UNKNOWN"
                rid = id_map.get((rn_norm, rt))
                if not rid:
                    continue
                for cid in m["source_chunk_ids"]:
                    pairs.append((rid, cid))

            effect_dao.bind_effect_chunks_bulk(conn, pairs)
            conn.commit()

        n_saved = len(id_map)
        print(f"[effects] page={page} SAVED: "
              f"effects={n_saved}, refs={len(pairs)}")
        return n_saved