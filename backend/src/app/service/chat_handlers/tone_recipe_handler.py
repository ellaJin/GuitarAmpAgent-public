# app/service/chat_handlers/tone_recipe_handler.py
import re
from typing import Any, Dict, Optional, List, Tuple

from app.llm.tool_factory import ToolFactory
from app.llm.guitar_fx_agent.config import get_llm
import json
from app.schemas.tone_recipe import ToneRecipe
from app.llm.prompts.tone_recipe import (
    TONE_RECIPE_QUERY_HINT,
    ToneRecipeJsonPromptParams,
    build_tone_recipe_prompt,
    build_json_retry_prompt,
)

RAG_TOOL_NAME = "search_guitar_manuals"
RAG_SNIPPET_MAX_CHARS = 3500

# 极小的“污染关键词”过滤（可以按需要再加）
RAG_POLLUTION_PATTERNS = [
    re.compile(r"\bBased on\b", re.IGNORECASE),
    re.compile(r"\bCONTROLS\b", re.IGNORECASE),
]


def _tool_name(t: Any) -> str:
    return getattr(t, "name", None) or getattr(t, "__name__", None) or str(t)


def _format_device_name(active_device: Any) -> str:
    if isinstance(active_device, dict):
        brand = (active_device.get("brand") or "").strip()
        model = (active_device.get("model") or "").strip()
        variant = (active_device.get("variant") or "").strip()
        name = f"{brand} {model}".strip()
        if variant:
            name += f" ({variant})"
        return name or "Unknown device"
    if isinstance(active_device, str) and active_device.strip():
        return active_device.strip()
    return "Unknown device"


def _find_tool(tools: List[Any], name: str) -> Optional[Any]:
    for t in tools or []:
        if getattr(t, "name", "") == name:
            return t
    return None


async def _call_tool_any(tool: Any, payload: Dict[str, Any]) -> str:
    if hasattr(tool, "ainvoke"):
        out = await tool.ainvoke(payload)
        return out if isinstance(out, str) else str(out)

    if hasattr(tool, "invoke"):
        out = tool.invoke(payload)
        return out if isinstance(out, str) else str(out)

    if hasattr(tool, "run"):
        out = tool.run(payload)
        return out if isinstance(out, str) else str(out)

    if callable(tool):
        out = tool(payload)
        if hasattr(out, "__await__"):
            out = await out
        return out if isinstance(out, str) else str(out)

    return str(tool)


async def _run_rag(rag_tool: Any, query: str) -> str:
    payload_candidates = [{"query": query}, {"q": query}, {"text": query}]
    last_err: Optional[Exception] = None
    for payload in payload_candidates:
        try:
            return await _call_tool_any(rag_tool, payload)
        except Exception as e:
            last_err = e
    raise RuntimeError(
        f"search_guitar_manuals failed. tried_payloads={payload_candidates}. "
        f"error={type(last_err).__name__}: {last_err}"
    )


def _is_rag_error_text(s: str) -> bool:
    s = (s or "").strip()
    return s.startswith("知识库检索异常") or s.startswith("在当前设备的知识库中未找到")


def _normalize_rag_snippet(text: str) -> str:
    s = (text or "").strip()
    if _is_rag_error_text(s):
        return s
    # 轻过滤：把明显污染的行删掉（不依赖 DB 层过滤也能改善）
    lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
    cleaned: List[str] = []
    for ln in lines:
        if any(p.search(ln) for p in RAG_POLLUTION_PATTERNS):
            continue
        cleaned.append(ln)
    s2 = "\n".join(cleaned)
    if len(s2) > RAG_SNIPPET_MAX_CHARS:
        s2 = s2[:RAG_SNIPPET_MAX_CHARS]
    return s2


def _extract_allow_lists(manual: str) -> Tuple[List[str], List[str], List[str]]:
    """
    从手册片段里抽 Delay/Reverb 类型 & Gate 模块名（轻量规则）
    目标：减少 hallucination，不追求完美。
    """
    t = manual or ""
    t_low = t.lower()

    # Gate names（你 preview 里出现过 Intel Reducer / Noise Gate）
    gate_names = []
    for name in ["Intel Reducer", "Noise Gate", "Noise Killer", "Noise Reducer"]:
        if name.lower() in t_low:
            gate_names.append(name)
    gate_names = list(dict.fromkeys(gate_names))  # 去重保序

    # Delay types：优先匹配常见关键字（你设备一般都有这些）
    delay_types = []
    for kw in ["Digital", "Analog", "Tape", "Pingpong", "Ping-pong", "Mod", "Reverse", "Dotted", "Stereo"]:
        if kw.lower() in t_low:
            delay_types.append(kw.replace("Ping-pong", "Pingpong"))
    delay_types = list(dict.fromkeys(delay_types))

    # Reverb types：Room/Hall/Plate/Spring/Church/Cave/Mod 等
    reverb_types = []
    for kw in ["Room", "Hall", "Plate", "Spring", "Church", "Cave", "Mod", "Arena"]:
        if kw.lower() in t_low:
            reverb_types.append(kw)
    reverb_types = list(dict.fromkeys(reverb_types))

    return delay_types, reverb_types, gate_names


def _validate_output(text: str) -> List[str]:
    """
    最小产品校验：确保结构齐全、换行存在。
    不合格则返回问题列表，用于自动重试。
    """
    problems: List[str] = []
    s = (text or "").strip()

    if "Song:" not in s or "Device:" not in s:
        problems.append("Missing 'Song:' or 'Device:' header lines.")
    if "Rhythm (clean-ish):" not in s:
        problems.append("Missing 'Rhythm (clean-ish):' section.")
    if "Solo (driven):" not in s:
        problems.append("Missing 'Solo (driven):' section.")
    if "Chain:" not in s:
        problems.append("Missing 'Chain:' block.")
    if "Key settings (suggested ranges):" not in s:
        problems.append("Missing 'Key settings (suggested ranges):' block.")
    if "\n" not in s:
        problems.append("No newline characters found; output must be multi-line as template.")
    if "**" in s:
        problems.append("Contains Markdown bold (**). Output must be plain text.")
    if "Based on" in s:
        problems.append("Contains 'Based on' preset/model naming; prohibited unless in manual snippet.")
    return problems


async def _invoke_llm(prompt: str) -> str:
    model = get_llm()
    out = await model.ainvoke(prompt) if hasattr(model, "ainvoke") else model.invoke(prompt)
    return getattr(out, "content", None) or str(out)


async def handle_tone_recipe(req, ctx) -> str:
    tools = ToolFactory.get_tools(ctx.user_id, ctx.kb_source_id) or []
    print("[tone] tools_count =", len(tools))
    print("[tone] tools_names =", [_tool_name(t) for t in tools])

    rag_tool = _find_tool(tools, RAG_TOOL_NAME)
    if rag_tool is None:
        return (
            "TONE_RECIPE: 没找到工具 search_guitar_manuals。\n"
            f"tools={[_tool_name(t) for t in tools]}\n"
            "请检查 ToolFactory.get_tools 是否在当前 kb_source_id 下注册了该工具。"
        )

    song = (req.user_input or "").strip()
    device_name = _format_device_name(getattr(ctx, "active_device", None))

    # 关键：RAG query 不带 song（只拿设备约束）
    rag_query = f"{device_name} {TONE_RECIPE_QUERY_HINT}"
    print("[tone] rag_query =", rag_query)

    try:
        rag_text = await _run_rag(rag_tool, rag_query)
    except Exception as e:
        return f"TONE_RECIPE: 调用 search_guitar_manuals 失败：{type(e).__name__}: {e}"

    rag_snippet = _normalize_rag_snippet(rag_text)
    print("[tone] rag_len =", len(rag_snippet))

    if _is_rag_error_text(rag_snippet):
        return f"TONE_RECIPE: {rag_snippet}"

    delay_types, reverb_types, gate_names = _extract_allow_lists(rag_snippet)
    print("[tone] allow_delay =", delay_types)
    print("[tone] allow_reverb =", reverb_types)
    print("[tone] allow_gate =", gate_names)

    prompt = build_tone_recipe_prompt(
        ToneRecipeJsonPromptParams(
            song=song,
            device_name=device_name,
            manual_snippet=rag_snippet,
            delay_types=delay_types,
            reverb_types=reverb_types,
            gate_names=gate_names,
        )
    )

    # 第一次生成
    text = await _invoke_llm(prompt)
    if text.strip() == "FORMAT_ERROR":
        return "TONE_RECIPE: 生成失败（FORMAT_ERROR），请重试或换个问法。"
    # 1) 先用 Pydantic 严格解析 JSON

    try:
        recipe = ToneRecipe.model_validate_json(text)
    except Exception as e1:
        # 2) retry 一次：强制 JSON-only
        retry_prompt = build_json_retry_prompt(prompt, f"{type(e1).__name__}: {e1}")
        text2 = await _invoke_llm(retry_prompt)
        recipe = ToneRecipe.model_validate_json(text2)

    # 3) 稳定渲染为多行文本（不再依赖模型换行）
    return recipe.to_text()
