# app/llm/prompts/midi_page_prompt_builder.py
"""
Shared page-level prompt builder for MIDI extraction.
Each brand strategy only provides brand-specific sections;
common rules (output format, grounding, filtering) live here.
"""
from __future__ import annotations

from typing import List, Optional


def build_midi_page_prompt(
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
        brand_context:     brand-specific block (message types, table format, special rules)
        page_number:       optional page number for logging context
    """
    indices_str = ", ".join(str(i) for i in allowed_indices)

    return f"""You extract MIDI mapping entries from a guitar multi-effects device manual page.

## Device: {device_name}

{brand_context}

## Input format
- You are given chunks from the same page, each with:
  - chunk_index (integer): use this to reference source chunks
  - page (number or null)
  - section (string or null)
  - text (string)

## GROUNDING RULES (MUST FOLLOW)
1) Every source_chunk_indices value MUST be one of: [{indices_str}]
2) Do NOT invent indices. Only use values from the list above.
3) If you cannot ground an entry to at least one valid index, DO NOT output it.
4) Only extract entries explicitly present in the text. Do not guess.

## FILTER RULES
- Only extract rows that describe a MIDI message assignment (CC, PC, or Bank Select).
- target_name length must be 1-60 characters.
- Do NOT extract global device settings (e.g. "MIDI channel = 1" as a device global).
- Prefer entries from tables, numbered lists, or dedicated MIDI/Command Center sections.

## FIELD DEFINITIONS
- message_type: "CC" (Control Change), "PC" (Program Change), or "BANK" (Bank Select)
- midi_channel:  integer 1-16, or null if not specified / applies to all channels
- cc_number:     integer 0-127 (only for CC messages)
- pc_number:     integer 0-127 (only for PC messages)
- bank_msb:      integer 0-127 (only for BANK messages, MSB byte)
- bank_lsb:      integer 0-127 (only for BANK messages, LSB byte)
- value_min:     integer 0-127 (minimum CC value, or null)
- value_max:     integer 0-127 (maximum CC value, or null)
- target_type:   category of what this MIDI message controls (see brand context)
- target_name:   exact name of the target (switch name, effect name, parameter name, etc.)
- target_path:   optional dot-path for nested targets (e.g. "Snapshot.1" or "Block.A")
- raw_description: brief description of what the mapping does (from the text, or null)

## OUTPUT FORMAT
- Output MUST be VALID JSON ONLY. No markdown, no backticks, no commentary.
- Return exactly one JSON object with key "midi_mappings".
- If no MIDI entries found, return: {{"midi_mappings": []}}

## JSON SCHEMA
{{"midi_mappings": [
  {{
    "message_type": "CC",
    "midi_channel": null,
    "cc_number": 64,
    "pc_number": null,
    "bank_msb": null,
    "bank_lsb": null,
    "value_min": 0,
    "value_max": 127,
    "target_type": "FOOTSWITCH",
    "target_name": "FS3",
    "target_path": null,
    "raw_description": "string or null",
    "confidence": 0.9,
    "source_chunk_indices": [0],
    "meta": {{}}
  }}
]}}

## Input chunks (JSON):
{page_chunks_json}
""".strip()
