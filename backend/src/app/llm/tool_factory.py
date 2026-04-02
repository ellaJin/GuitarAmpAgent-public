# app/llm/tool_factory.py
import json
from typing import Any, List, Optional

from langchain_core.tools import tool

from app.schemas.device import ActiveDeviceContext
from app.llm.tools.rag_tool import search_local_docs_logic
from app.llm.tools.effect_kb_tool import search_effect_kb_logic


def _extract_query(inp: Any) -> str:
    """
    Accept:
    - plain string
    - dict {"query": "..."} / {"q": "..."} / {"text": "..."}
    - JSON string like '{"query":"..."}'
    """
    if inp is None:
        return ""

    if isinstance(inp, str):
        s = inp.strip()
        if s.startswith("{") and s.endswith("}"):
            try:
                obj = json.loads(s)
                if isinstance(obj, dict):
                    return (obj.get("query") or obj.get("q") or obj.get("text") or "").strip()
            except Exception:
                return s
        return s

    if isinstance(inp, dict):
        return (inp.get("query") or inp.get("q") or inp.get("text") or "").strip()

    return str(inp).strip()


class ToolFactory:
    @staticmethod
    def get_tools(user_id: str, active_device: Optional[ActiveDeviceContext]) -> List:
        if not active_device:
            return []

        kb_source_id = active_device.kb_source_id
        device_model_id = active_device.device_model_id

        tools: List = []

        @tool("search_manual_chunks")
        def search_manual_chunks(inp: Any) -> str:
            """
            The ONLY source of truth for the ACTIVE DEVICE manual.
            You MUST use this tool for ALL hardware-related questions, including:
            - Hardware specs (Battery, 9V Power, Voltage, Polarity).
            - Physical connections (I/O routing, FX LOOP, Send/Return).
            - System settings (Menu paths, Calibration, Firmware).
            - Troubleshooting and technical limitations.
            DO NOT rely on your pre-trained knowledge—even for simple questions like
            'Does it support 9V battery?'. Always verify with this tool first.
            """
            q = _extract_query(inp)
            if not q:
                return "在当前设备的知识库中未找到相关信息。"
            return search_local_docs_logic(query=q, user_id=user_id, kb_source_id=kb_source_id)

        tools.append(search_manual_chunks)

        @tool("search_effect_kb")
        def search_effect_kb(inp: Any) -> str:
            """
            Search the ACTIVE DEVICE structured effects KB (raw_effect_entries).
            Use for module lists (delay/dist/chorus), effect descriptions, etc.
            """
            q = _extract_query(inp)
            if not q:
                return json.dumps({"items": [], "meta": {"reason": "empty_query"}}, ensure_ascii=False)

            return search_effect_kb_logic(
                query=q,
                user_id=user_id,
                device_model_id=device_model_id,
                kb_source_id=kb_source_id,
                top_k=8,
            )

        tools.append(search_effect_kb)

        return tools
