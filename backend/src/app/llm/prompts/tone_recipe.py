# app/llm/prompts/tone_recipe_json.py
from dataclasses import dataclass
from typing import List

TONE_RECIPE_QUERY_HINT = (
    "effect modules list signal chain "
    "noise gate threshold "
    "compressor sustain level "
    "overdrive distortion gain tone level "
    "amp model cab ir loader "
    "eq bass mid treble frequency "
    "delay type time ms feedback mix "
    "reverb type decay mix pre-delay"
)

@dataclass(frozen=True)
class ToneRecipeJsonPromptParams:
    song: str
    device_name: str
    manual_snippet: str
    delay_types: List[str]
    reverb_types: List[str]
    gate_names: List[str]

def build_tone_recipe_prompt(p: ToneRecipeJsonPromptParams) -> str:
    return f"""
You are GuitarFX-Agent. Generate a practical starting tone recipe for the requested song.

HARD RULES:
- KB contains ONLY device manual. Do not claim official song settings.
- You MUST obey allow-lists. If a type is not allowed, choose one that IS allowed.
- Output MUST be VALID JSON ONLY. No extra text. No Markdown.
- If you cannot comply, output exactly: FORMAT_ERROR

ALLOW-LISTS:
- delay_types_allowed: {p.delay_types}
- reverb_types_allowed: {p.reverb_types}
- gate_names_allowed: {p.gate_names}

[Device Manual Snippet]
{p.manual_snippet}

[Request]
song = {p.song}
device = {p.device_name}

[JSON SCHEMA]
{{
  "song": "string",
  "device": "string",
  "rhythm": {{
    "chain": [
      {{"module":"string","state":"ON|OFF","type_or_model":"string|null"}}
    ],
    "ranges": {{
      "gain_drive": "x–y",
      "eq": "free text",
      "delay": "free text",
      "reverb": "free text",
      "gate_nr": "free text"
    }},
    "notes": ["string"]
  }},
  "solo": {{
    "chain": [
      {{"module":"string","state":"ON|OFF","type_or_model":"string|null"}}
    ],
    "ranges": {{
      "gain_drive": "x–y",
      "eq": "free text",
      "delay": "free text",
      "reverb": "free text",
      "gate_nr": "free text"
    }},
    "notes": ["string"]
  }}
}}
""".strip()

def build_json_retry_prompt(original_prompt: str, reason: str) -> str:
    return (
        original_prompt
        + "\n\nYour previous output was invalid.\n"
        + f"Reason: {reason}\n"
        + "Rewrite and output VALID JSON ONLY matching the schema. No extra text."
    )
