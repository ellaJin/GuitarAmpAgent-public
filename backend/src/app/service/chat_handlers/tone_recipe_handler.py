# app/service/chat_handlers/tone_recipe_handler.py
import re
from typing import Any, Dict, Optional, List, Tuple

from app.llm.tool_factory import ToolFactory
from app.llm.guitar_fx_agent.config import get_llm
from app.service.chat_router import has_song_reference
from app.db import get_db_con
from app.dao.effect_kb_dao import query_allow_list_entries
import json
from app.schemas.tone_recipe import ToneRecipe
from app.llm.prompts.tone_recipe import (
    TONE_RECIPE_QUERY_HINT,
    ToneRecipeJsonPromptParams,
    build_tone_recipe_prompt,
    build_json_retry_prompt,
)

RAG_TOOL_NAME = "search_manual_chunks"
RAG_SNIPPET_MAX_CHARS = 3500

# raw_type spelling isn't consistent across brand extraction strategies —
# verified against the live DB, not guessed. Delay/reverb are named
# differently per brand; real noise-gate modules are all tagged DYNAMICS
# (which also contains compressors — a known imprecision in the source data).
DELAY_TYPES = ("DLY", "DELAY")
REVERB_TYPES = ("REV", "REVERB")
GATE_TYPES = ("DYNAMICS",)
# DYNAMICS also holds compressors (Mooer/Helix extraction strategies file
# both under the same category) — raw_type alone can't tell them apart, so
# filter by name too. Verified against every live DYNAMICS row: catches
# every real gate ("Noise Gate", "Hard Gate", "Horizon Gate", "Intel
# Reducer", "Noise Killer") and excludes every compressor (e.g. "Red Comp").
GATE_NAME_KEYWORDS = ("gate", "noise", "reducer", "killer", "suppress")

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
    # Handle Pydantic model (ActiveDeviceContext)
    brand = (getattr(active_device, "brand", "") or "").strip()
    model = (getattr(active_device, "model", "") or "").strip()
    name = f"{brand} {model}".strip()
    return name or "Unknown device"


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
    payload_candidates = [{"inp": query}, {"query": query}, {"q": query}, {"text": query}]
    last_err: Optional[Exception] = None
    for payload in payload_candidates:
        try:
            return await _call_tool_any(rag_tool, payload)
        except Exception as e:
            last_err = e
    raise RuntimeError(
        f"search_manual_chunks failed. tried_payloads={payload_candidates}. "
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


def _fetch_type_allow_list(device_model_id: str, raw_types: Tuple[str, ...]) -> List[str]:
    """
    Ground-truth module/type names for a delay/reverb/gate-style category,
    queried directly from raw_effect_entries. Callers pass every known
    raw_type spelling for the category (see DELAY_TYPES/REVERB_TYPES/
    GATE_TYPES above) since the spelling isn't consistent across brands.
    """
    with get_db_con() as conn:
        rows = query_allow_list_entries(conn, device_model_id=device_model_id, raw_types=raw_types)
    return [r[1] for r in rows]


def _fetch_amp_cab_allow_lists(device_model_id: str) -> Tuple[List[str], List[str]]:
    """
    Ground-truth AMP/CAB module names for this device, queried directly from
    raw_effect_entries (see query_allow_list_entries). Scoped by device_model_id
    only — not kb_source_id — since a device's module list can be split
    across several ingested manuals. No text-matching fallback: if the
    device has no AMP/CAB rows in the KB, the allow-list stays empty and the
    prompt must not name a model for that slot.
    """
    with get_db_con() as conn:
        rows = query_allow_list_entries(conn, device_model_id=device_model_id, raw_types=("AMP", "CAB"))
    amp_models = [r[1] for r in rows if r[3] == "AMP"]
    cab_names = [r[1] for r in rows if r[3] == "CAB"]
    return amp_models, cab_names


def _enforce_amp_cab_allow_list(recipe: ToneRecipe, amp_models: List[str], cab_names: List[str]) -> None:
    """
    Deterministic post-parse cleanup, run once after JSON parsing succeeds:
    - Drop the AMP/CAB chain step entirely when its allow-list is empty —
      we have no ground-truth name for that module on this device, and a
      nameless "AMP: ON" line is worse than not mentioning it at all. "No
      rows for this raw_type" can't distinguish "device has no such
      module" from "extraction missed it", but the right on-screen result
      is the same either way, so no such distinction is made here.
    - Null out type_or_model for any remaining step whose state is OFF —
      an inactive module should not carry a type/model name. Enforced here
      rather than via prompt wording alone, since that isn't reliable on
      its own.
    - Null out any AMP/CAB type_or_model that isn't in the allow-list.
    """
    allowed = {
        "AMP": {n.upper() for n in amp_models},
        "CAB": {n.upper() for n in cab_names},
    }
    for section in (recipe.rhythm, recipe.solo):
        kept_steps = []
        for step in section.chain:
            module = step.module.strip().upper()
            if module in allowed and not allowed[module]:
                continue  # no ground-truth names for this module — drop the line
            if step.state == "OFF":
                step.type_or_model = None
            elif module in allowed:
                value = (step.type_or_model or "").strip().upper()
                if value not in allowed[module]:
                    step.type_or_model = None
            kept_steps.append(step)
        section.chain = kept_steps


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


def _strip_code_fences(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
        s = re.sub(r"\n?```$", "", s)
    return s.strip()


async def _invoke_llm(prompt: str) -> Tuple[str, int]:
    model = get_llm()
    out = await model.ainvoke(prompt) if hasattr(model, "ainvoke") else model.invoke(prompt)
    raw = getattr(out, "content", None) or str(out)
    usage = getattr(out, "usage_metadata", None)
    if usage is None:
        print("[tone] WARNING: usage_metadata missing on LLM response")
    tokens = (usage.get("total_tokens") or 0) if usage else 0
    return _strip_code_fences(raw), tokens


async def handle_tone_recipe(req, ctx) -> Tuple[str, int, bool]:
    accumulator = {"source_count": 0}
    tools = ToolFactory.get_tools(ctx.user_id, ctx.active_device, accumulator) or []
    print("[tone] tools_count =", len(tools))
    print("[tone] tools_names =", [_tool_name(t) for t in tools])

    rag_tool = _find_tool(tools, RAG_TOOL_NAME)
    if rag_tool is None:
        return (
            "TONE_RECIPE: 没找到工具 search_guitar_manuals。\n"
            f"tools={[_tool_name(t) for t in tools]}\n"
            "请检查 ToolFactory.get_tools 是否在当前 kb_source_id 下注册了该工具。"
        ), 0, False

    song = (req.user_input or "").strip()

    # Belt-and-braces, independent of chat_router's dispatch decision: even
    # if this handler is ever reached without a real song reference (a
    # routing bug, or a future caller bypassing chat_router), don't let the
    # raw question fall into the recipe's song field.
    if not has_song_reference(song.lower()):
        return (
            "TONE_RECIPE: I couldn't identify a specific song in your question, "
            "so I can't generate a tone recipe for it. Please name the song "
            "(and ideally the artist) -- e.g. \"tone for Nothing Else Matters by "
            "Metallica\". For general manual or settings questions, just ask directly.",
            0,
            False,
        )

    device_name = _format_device_name(getattr(ctx, "active_device", None))
    device_model_id = ctx.active_device.device_model_id

    # Ground-truth module names for this device, independent of the
    # manual-chunk RAG lookup below.
    amp_models, cab_names = _fetch_amp_cab_allow_lists(device_model_id)
    delay_types = _fetch_type_allow_list(device_model_id, DELAY_TYPES)
    reverb_types = _fetch_type_allow_list(device_model_id, REVERB_TYPES)
    gate_names = [
        n for n in _fetch_type_allow_list(device_model_id, GATE_TYPES)
        if any(kw in n.lower() for kw in GATE_NAME_KEYWORDS)
    ]
    print("[tone] allow_delay =", delay_types)
    print("[tone] allow_reverb =", reverb_types)
    print("[tone] allow_gate =", gate_names)

    # 关键：RAG query 不带 song（只拿设备约束）
    rag_query = f"{device_name} {TONE_RECIPE_QUERY_HINT}"
    print("[tone] rag_query =", rag_query)

    try:
        rag_text = await _run_rag(rag_tool, rag_query)
    except Exception as e:
        return f"TONE_RECIPE: 调用 search_guitar_manuals 失败：{type(e).__name__}: {e}", 0, False

    rag_snippet = _normalize_rag_snippet(rag_text)
    print("[tone] rag_len =", len(rag_snippet))

    if _is_rag_error_text(rag_snippet):
        return f"TONE_RECIPE: {rag_snippet}", 0, False

    prompt = build_tone_recipe_prompt(
        ToneRecipeJsonPromptParams(
            song=song,
            device_name=device_name,
            manual_snippet=rag_snippet,
            delay_types=delay_types,
            reverb_types=reverb_types,
            gate_names=gate_names,
            amp_models=amp_models,
            cab_names=cab_names,
        )
    )

    # 第一次生成
    text, tokens_used = await _invoke_llm(prompt)
    if text.strip() == "FORMAT_ERROR":
        return (
            "TONE_RECIPE: I wasn't able to generate a valid tone recipe for that "
            "request. Try rephrasing -- naming the song and artist directly usually "
            "helps, e.g. \"tone for Sweet Child O' Mine by Guns N' Roses\".",
            tokens_used,
            False,
        )
    # 1) 先用 Pydantic 严格解析 JSON

    try:
        recipe = ToneRecipe.model_validate_json(text)
    except Exception as e1:
        # 2) retry 一次：强制 JSON-only
        retry_prompt = build_json_retry_prompt(prompt, f"{type(e1).__name__}: {e1}")
        text2, tokens2 = await _invoke_llm(retry_prompt)
        tokens_used += tokens2
        recipe = ToneRecipe.model_validate_json(text2)

    # 3) Hard backstop: strip any AMP/CAB name not on this device's real
    #    module list, so a hallucinated model name never reaches the user.
    _enforce_amp_cab_allow_list(recipe, amp_models, cab_names)

    # 4) 稳定渲染为多行文本（不再依赖模型换行）
    return recipe.to_text(), tokens_used, True
