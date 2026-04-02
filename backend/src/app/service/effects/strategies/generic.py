# app/service/effects/strategies/generic.py
"""Generic fallback strategy for unrecognized brands."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.service.effects.strategies.base import BrandExtractStrategy, BrandMatchResult
from app.llm.prompts.effect_page_prompt_builder import build_effect_page_prompt


class GenericFallbackStrategy(BrandExtractStrategy):
    """
    Used when no brand-specific strategy matches.
    Broader prompt, conservative confidence, minimal post-processing.
    """

    def brand_key(self) -> str:
        return "generic"

    def match(self, device_name: str, brand_hint: str = "", sample_text: str = "") -> Optional[BrandMatchResult]:
        return None

    _BRAND_CONTEXT = """## General rules
- Extract effect MODEL NAMES from tables or lists
- raw_name = the model/effect name as shown in the device (short name, NOT the "based on" reference)
- raw_type = the category (DISTORTION, AMP, CAB, MODULATION, DELAY, REVERB, EQ, DYNAMICS, WAH, PITCH, FILTER, or UNKNOWN)
- raw_description = any description or "based on" info
- SKIP: operating instructions, parameter descriptions, connection diagrams, troubleshooting
- confidence: 0.8 for clear entries, 0.5 for uncertain"""

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

    def post_process(self, modules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return modules