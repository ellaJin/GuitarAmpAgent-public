# app/service/effects/llm_effect_extractor.py
import json
import re
from typing import Any, Dict, List, Optional, Union

from app.service.effects.extractor_base import EffectExtractor


def _extract_json_obj_or_array(text: str) -> Optional[str]:
    """
    Accept:
      - {"modules":[...]}
      - [...]
    Also handles ```json ...``` fenced blocks.
    """
    if not text:
        return None
    t = text.strip()

    # fenced first
    m = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", t, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1)

    # try object
    m = re.search(r"(\{.*\})", t, re.DOTALL)
    if m:
        return m.group(1)

    # try array
    m = re.search(r"(\[\s*\{.*?\}\s*\])", t, re.DOTALL)
    if m:
        return m.group(1)

    if (t.startswith("{") and t.endswith("}")) or (t.startswith("[") and t.endswith("]")):
        return t

    return None


class LLMEffectExtractor(EffectExtractor):
    """
    Page-mode extractor.
    Input: full prompt string (built by strategy + prompt builder).
    Output: dict {"modules": [...]}
    """

    def __init__(
        self,
        llm,
        device_name: str = "Device",
        **kwargs,
    ):
        self.llm = llm
        self.device_name = device_name

    def extract(self, text: str, *, mode: str = "page", output_key: str = "modules") -> Dict[str, Any]:
        """
        Page mode: treat `text` as FULL prompt, returns Dict {output_key: [...]}
        output_key defaults to "modules" (effect pipeline).
        Pass output_key="midi_mappings" for the MIDI pipeline.
        """
        if not text or len(text.strip()) < 50:
            return {output_key: []}

        msg = self.llm.invoke(text)
        resp = getattr(msg, "content", None) or str(msg)

        json_str = _extract_json_obj_or_array(resp)
        if not json_str:
            retry = (
                text
                + "\n\nYour previous output was invalid.\n"
                + "Rewrite and output VALID JSON ONLY matching the schema. No extra text."
            )
            msg2 = self.llm.invoke(retry)
            resp2 = getattr(msg2, "content", None) or str(msg2)
            json_str = _extract_json_obj_or_array(resp2)
            if not json_str:
                return {output_key: []}

        try:
            data: Union[Dict[str, Any], List[Any]] = json.loads(json_str)
        except Exception:
            return {output_key: []}

        if isinstance(data, dict):
            mods = data.get(output_key, [])
            if isinstance(mods, list):
                return {output_key: [m for m in mods if isinstance(m, dict)]}
            return {output_key: []}

        if isinstance(data, list):
            return {output_key: [m for m in data if isinstance(m, dict)]}

        return {output_key: []}

    def invoke_prompt(self, prompt: str) -> str:
        msg = self.llm.invoke(prompt)
        return getattr(msg, "content", None) or str(msg)