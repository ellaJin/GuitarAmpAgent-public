# app/service/effects/strategies/boss_gt.py
"""Boss GT series strategy (GT-1, GT-100, GT-1000, etc.)"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.service.effects.strategies.base import BrandExtractStrategy, BrandMatchResult
from app.llm.prompts.effect_page_prompt_builder import build_effect_page_prompt


class BossGTStrategy(BrandExtractStrategy):

    def brand_key(self) -> str:
        return "boss_gt"

    # ------------------------------------------------------------------ match
    def match(
        self,
        device_name: str,
        brand_hint: str = "",
        sample_text: str = "",
    ) -> Optional[BrandMatchResult]:
        dn = (device_name or "").lower()
        bh = (brand_hint or "").lower()
        st = (sample_text or "").lower()

        if "boss" in bh:
            return BrandMatchResult(
                brand_key=self.brand_key(),
                confidence=0.9,
                device_family="Boss GT",
            )

        if re.search(r"boss.*gt[-\s]?\d+", dn) or re.search(r"boss.*gt[-\s]?\d+", st):
            return BrandMatchResult(
                brand_key=self.brand_key(),
                confidence=0.9,
                device_family="Boss GT",
            )

        if "boss" in dn and any(kw in st for kw in ("parameter guide", "patch", "effect type")):
            return BrandMatchResult(
                brand_key=self.brand_key(),
                confidence=0.7,
                device_family="Boss Unknown",
            )

        return None

    # ------------------------------------------------------------- page gate
    _PAGE_KEYWORDS = frozenset({
        "effect type", "parameter guide", "od/ds", "preamp",
        "comp", "delay", "reverb", "mod", "eq", "fx",
        "noise suppressor", "pedal fx", "foot volume",
        "cosm amp", "speaker type",
    })

    def should_process_page(self, page_chunks: List[Dict[str, Any]]) -> bool:
        combined = self._combine_chunk_text(page_chunks)
        if any(kw in combined for kw in self._PAGE_KEYWORDS):
            return True
        return self._check_section_metadata(
            page_chunks, ("effect", "amp", "preamp", "parameter"),
        )

    # --------------------------------------------------------------- prompt
    _BRAND_CONTEXT = """## Boss GT Manual Structure
Boss manuals list effects by category with parameters. Categories (use as raw_type):
- OD/DS (overdrive/distortion)
- AMP (COSM amp models)
- SPEAKER (speaker cabinet simulations)
- COMP (compressor)
- MOD (modulation)
- DLY (delay)
- REV (reverb)
- EQ (equalizer)
- FX (special effects: harmonist, octave, etc.)
- NS (noise suppressor)

## Extraction rules
- raw_name = the effect type name (e.g. "OD-1", "BLUES", "METAL ZONE")
- raw_type = category from section header
- raw_description = parameter info or "based on" reference if available
- SKIP parameter descriptions, only extract effect TYPE names"""

    def build_page_prompt(
        self,
        device_name: str,
        page_chunks_json: str,
        page_number=None,
        allowed_indices: list[int] | None = None,
    ) -> str:
        return build_effect_page_prompt(
            device_name=device_name,
            page_chunks_json=page_chunks_json,
            allowed_indices=allowed_indices or [],
            brand_context=self._BRAND_CONTEXT,
            page_number=page_number,
        )

    # --------------------------------------------------------- post-process
    _TYPE_MAP = {
        "OD/DS": "DS", "OD": "DS", "DISTORTION": "DS",
        "COMP": "DYNAMICS", "COMPRESSOR": "DYNAMICS",
        "SPEAKER": "CAB",
    }

    def post_process(self, modules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for m in modules:
            rt = (m.get("raw_type") or "UNKNOWN").upper().strip()
            m["raw_type"] = self._TYPE_MAP.get(rt, rt)
        return modules