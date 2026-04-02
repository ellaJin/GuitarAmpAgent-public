# app/llm/prompts/effect_page_prompt_builder.py
"""
Shared page-level prompt builder for effect extraction.
Each brand strategy only provides brand-specific sections;
common rules (output format, grounding, filtering) live here.
"""
from __future__ import annotations

from typing import List, Optional


def build_effect_page_prompt(
    *,
    device_name: str,
    page_chunks_json: str,
    allowed_indices: List[int],
    brand_context: str,
    page_number: Optional[int | str] = None,
) -> str:
    """
    Args:
        device_name:       device name shown to LLM
        page_chunks_json:  JSON string of [{chunk_index, page, section, text}, ...]
        allowed_indices:   list of valid chunk_index values [0, 1, 2, ...]
        brand_context:     brand-specific block (categories, table format, special rules)
        page_number:       optional page number for logging context
    """
    indices_str = ", ".join(str(i) for i in allowed_indices)

    return f"""You extract guitar multi-effects SELECTABLE MODEL ENTRIES from a device manual page.

## Device: {device_name}

{brand_context}

## Input format
- You are given chunks from the same page, each with:
  - chunk_index (integer): use this to reference source chunks
  - page (number or null)
  - section (string or null)
  - text (string)

## TERMINOLOGY NOTE
The manual may NOT use the word "module".
It may use terms like: model, effect model, algorithm, block, FX list, effect list, annex,
or tables with columns like "No.", "Model name", "Description".
Treat all of these as the same concept: selectable entries in the device.

## GROUNDING RULES (MUST FOLLOW)
1) Every source_chunk_indices value MUST be one of: [{indices_str}]
2) Do NOT invent indices. Only use values from the list above.
3) If you cannot ground an entry to at least one valid index, DO NOT output it.
4) Only extract entries explicitly present in the text. Do not guess.

## FILTER RULES
- raw_name length must be 2-40 characters.
- raw_name must NOT contain instruction verbs (press/select/connect/turn/save/return/navigate/choose/set).
- raw_name must NOT be a full sentence.
- Prefer entries from tables, numbered lists, or annex/effect lists.

## OUTPUT FORMAT
- Output MUST be VALID JSON ONLY. No markdown, no backticks, no commentary.
- Return exactly one JSON object with key "modules".
- If no entries found, return: {{"modules": []}}

## JSON SCHEMA
{{"modules": [
  {{
    "raw_name": "string",
    "raw_type": "string",
    "raw_category": "string or null",
    "raw_description": "string or null",
    "confidence": 0.85,
    "source_chunk_indices": [0, 1],
    "meta": {{"evidence": "short quote <= 20 words"}}
  }}
]}}

## Input chunks (JSON):
{page_chunks_json}
""".strip()