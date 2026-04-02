# app/service/effects/strategies/mooer_ge.py
"""MOOER GE series strategy (GE150, GE200, GE250, GE300, etc.)"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.service.effects.strategies.base import BrandExtractStrategy, BrandMatchResult
from app.llm.prompts.effect_page_prompt_builder import build_effect_page_prompt


class MooerGEStrategy(BrandExtractStrategy):

    def brand_key(self) -> str:
        return "mooer_ge"

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

        if "mooer" in bh:
            return BrandMatchResult(
                brand_key=self.brand_key(),
                confidence=0.9,
                device_family=self._extract_family(dn or st),
            )

        if re.search(r"mooer.*ge\s?\d{3}", dn) or re.search(r"mooer.*ge\s?\d{3}", st):
            return BrandMatchResult(
                brand_key=self.brand_key(),
                confidence=0.9,
                device_family=self._extract_family(dn or st),
            )

        if "mooer" in dn and any(kw in st for kw in ("annex", "effect module", "fx miscellaneous")):
            return BrandMatchResult(
                brand_key=self.brand_key(),
                confidence=0.8,
                device_family="MOOER Unknown",
            )

        return None

    @staticmethod
    def _extract_family(text: str) -> str:
        m = re.search(r"ge\s?(\d{3})\s*(pro|li)?", text, re.IGNORECASE)
        if m:
            return f"GE{m.group(1)} {(m.group(2) or '').capitalize()}".strip()
        return "MOOER GE"

    # ------------------------------------------------------------- page gate
    _PAGE_KEYWORDS = frozenset({
        "annex", "effect module description", "fx miscellaneous",
        "overdrive", "distortion", "amplifier module", "cabinet module",
        "modulation module", "delay module", "reverb module",
        "noise gate", "noise killer", "eq module",
        "model name", "based on",
        "compressor", "chorus", "flanger", "phaser", "tremolo",
        "wah", "reverb", "cab", "amp",
    })

    def should_process_page(self, page_chunks: List[Dict[str, Any]]) -> bool:
        combined = self._combine_chunk_text(page_chunks)
        if any(kw in combined for kw in self._PAGE_KEYWORDS):
            return True
        return self._check_section_metadata(page_chunks, ("annex", "effect", "module"))

    # --------------------------------------------------------------- prompt
    _BRAND_CONTEXT = """## MOOER GE Manual Structure
The manual uses these module categories (use as raw_type):
- FX (wah, compressor effects)
- DS (overdrive/distortion pedal effects)
- AMP (amplifier simulations)
- CAB (cabinet simulations)
- NS (noise gate/reduction)
- EQ (equalizer)
- MOD (modulation: chorus, flanger, phaser, tremolo, etc.)
- DLY (delay effects)
- REV (reverb effects)

## Table format
Tables have columns: No. | Model name | Description
- "Model name" = the effect's raw_name (e.g. "Cry Wah", "808", "J800")
- "Description" = what it's based on (e.g. "Based on IBANEZ TS808")
- "No." = index within the category

## Extraction rules
- raw_name = the "Model name" column value (NOT the description/based-on name)
- raw_type = the module category from the section header (FX, DS, AMP, CAB, NS, EQ, MOD, DLY, REV)
- raw_description = the "Description" column value
- confidence: 0.9 for clear table entries, 0.7 for ambiguous ones
- SKIP non-effect entries like section headers, page numbers, footnotes"""

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
        "FX": "FX", "COMP": "FX",
        "DS": "DS", "OVERDRIVE": "DS", "DISTORTION": "DS",
        "AMP": "AMP", "AMPLIFIER": "AMP",
        "CAB": "CAB", "CABINET": "CAB",
        "NS": "NS", "NOISE": "NS", "GATE": "NS",
        "EQ": "EQ", "EQUALIZER": "EQ",
        "MOD": "MOD", "MODULATION": "MOD",
        "DLY": "DLY", "DELAY": "DLY",
        "REV": "REV", "REVERB": "REV",
        # LLM return
        "WAH": "FX",
        "DYNAMICS": "FX",
        "COMPRESSOR": "FX",
        "COMPRESSION": "FX",
    }

    _CATEGORY_MAP = {
        "FX": "FX miscellaneous",
        "DS": "DS overdrive / distortion",
        "AMP": "AMPlifier",
        "CAB": "CABinet",
        "NS": "NS noise gate",
        "EQ": "EQ",
        "MOD": "MODulation",
        "DLY": "DELAY",
        "REV": "REVERB",
    }

    def post_process(self, modules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for m in modules:
            rt = (m.get("raw_type") or "UNKNOWN").upper().strip()
            m["raw_type"] = self._TYPE_MAP.get(rt, rt)
            if not m.get("raw_category") or m["raw_category"] in (None, "", "null", "unknown"):
                m["raw_category"] = self._CATEGORY_MAP.get(m["raw_type"], m["raw_type"])
        return modules