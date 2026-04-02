# app/service/doc_processing/strategy_router.py
from typing import Any, Dict, Optional

from app.service.doc_processing.profiles import ChunkProfile, BOSS_FINE, HELIX_COARSE, DEFAULT_MED


def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()


# ---------------------------------------------------------------------------
# source_type contract (set by admin at upload time):
#
#   "effects_settings" — dedicated effect parameter PDF (e.g. Boss effect guide)
#                        → run effect pipeline, use fine chunking
#   "mixed"            — single PDF containing everything (e.g. Moore all-in-one manual)
#                        → run effect pipeline, use brand-based chunking
#   "user_manual"      — operation/setup guide, no effect list
#                        → skip effect pipeline, use medium chunking
#
# Add new source_type values here as new brands/doc types are onboarded.
# ---------------------------------------------------------------------------

_EFFECT_PIPELINE_SOURCE_TYPES = {"effects_settings", "mixed"}


def should_run_effect_pipeline(ctx: Dict[str, Any]) -> bool:
    """
    Return True if EffectExtractionPipeline should run for this document.

    Decision is driven entirely by source_type, which is set by the admin
    at upload time. No runtime inference is performed here.
    """
    source_type = _norm(ctx.get("source_type"))
    print(f"Source Type: {source_type}")
    used_effect_pipeline = source_type in _EFFECT_PIPELINE_SOURCE_TYPES
    print(f"Used Effect Pipeline: {used_effect_pipeline}")
    return used_effect_pipeline


def pick_profile(ctx: Dict[str, Any]) -> ChunkProfile:
    """
    Pick a ChunkProfile based on source_type, with brand as fallback.

    Priority:
      1. source_type  — most reliable signal (explicitly set at upload)
      2. brand        — fallback when source_type is missing or 'mixed'
      3. DEFAULT_MED  — safe fallback for unknown brands
    """
    brand = _norm(ctx.get("brand"))
    source_type = _norm(ctx.get("source_type"))

    # effects_settings: dedicated parameter docs should always use fine chunking
    # to keep individual effect definitions tight and retrievable
    if source_type == "effects_settings":
        return BOSS_FINE

    # user_manual: operation guides do not need fine granularity
    if source_type == "user_manual":
        return DEFAULT_MED

    # mixed (or unknown): fall back to brand-level defaults
    if "boss" in brand:
        return BOSS_FINE

    if "line 6" in brand or "line6" in brand or "helix" in brand:
        return HELIX_COARSE

    return DEFAULT_MED