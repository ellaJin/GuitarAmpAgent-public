# app/llm/prompts/song_config_extractor.py


def build_song_config_prompt(raw_text: str) -> str:
    return f"""You are a guitar effects expert. Extract the structured configuration from the following AI-generated guitar effects recommendation.

Return ONLY a valid JSON object matching this exact schema. Use null for any field that is not mentioned.

{{
  "amp_model": "string or null",
  "cab": "string or null",
  "effects": [
    {{
      "name": "string",
      "type": "Distortion | Delay | Reverb | Chorus | Compressor | EQ | Modulation | Other",
      "position": "pre | post | null",
      "parameters": {{}}
    }}
  ],
  "delay": {{
    "time": "string or null",
    "feedback": "integer 0-100 or null",
    "mix": "integer 0-100 or null",
    "type": "string or null"
  }},
  "reverb": {{
    "type": "string or null",
    "decay": "number or null",
    "mix": "integer 0-100 or null"
  }},
  "notes": "any additional important information or null"
}}

Guitar effects recommendation to parse:
---
{raw_text}
---

Return only the JSON object. No explanation, no markdown fences, no extra text."""
