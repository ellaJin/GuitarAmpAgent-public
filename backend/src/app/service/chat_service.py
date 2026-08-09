# app/service/chat_service.py
import json
import logging
from typing import Any, List, Tuple

from langchain_core.messages import AIMessage

from app.llm.tool_factory import ToolFactory
from app.llm.agents.deep_agent import build_deep_agent
from app.schemas.chat import ChatQueryRequest, ChatQueryContext
from app.utils.quality import compute_quality_flags

logger = logging.getLogger("quality")

from app.service.chat_router import (
    route_query,
    ROUTE_INVENTORY,
    ROUTE_MANUAL_QA,
    ROUTE_TONE_RECIPE,
    ROUTE_OTHER,
)
from app.db import get_db_con

from app.service.chat_handlers.inventory_handler import handle_inventory
from app.service.chat_handlers.manual_qa_handler import handle_manual_qa
from app.service.chat_handlers.tone_recipe_handler import handle_tone_recipe


def _history_to_messages(req: ChatQueryRequest) -> List[Tuple[str, str]]:
    messages: List[Tuple[str, str]] = []
    if not req.chat_history:
        return messages

    for m in req.chat_history:
        if m.role == "user":
            messages.append(("human", m.content))
        else:
            messages.append(("ai", m.content))
    return messages


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _sum_usage_tokens(msgs: List[Any]) -> int:
    total = 0
    for m in msgs:
        if not isinstance(m, AIMessage):
            continue
        usage = getattr(m, "usage_metadata", None)
        if usage:
            total += usage.get("total_tokens") or 0
        else:
            logger.warning(json.dumps({"event": "token_usage_missing", "handler": "deep_agent"}))
    return total


async def _run_deep_agent(req: ChatQueryRequest, ctx: ChatQueryContext) -> Tuple[str, int]:
    """
    你原来的 deep_agent 流程抽出来，方便 manual_qa handler 复用/将来扩展。
    """
    accumulator = {"source_count": 0}
    # tools = ToolFactory.get_tools(ctx.user_id, ctx.kb_source_id)
    tools = ToolFactory.get_tools(ctx.user_id, ctx.active_device, accumulator)
    graph = build_deep_agent(tools)

    print("[chat] tools_count =", len(tools))
    print("[chat] tools_names =", [getattr(t, "name", str(t)) for t in tools])

    context_system = (
        "Current User Context:\n"
        f"- User Name: {ctx.user_name}\n"
        f"- Active Device: {ctx.active_device}\n\n"
        f"Prioritize using tools for device: {ctx.active_device}."
    )

    messages = _history_to_messages(req)
    messages = [("system", context_system)] + messages
    messages.append(("human", req.user_input))

    result_state = await graph.ainvoke({"messages": messages})
    source_count = accumulator["source_count"]
    msgs = result_state.get("messages", [])
    tokens_used = _sum_usage_tokens(msgs)

    tool_names: List[str] = []
    for m in msgs:
        tc = getattr(m, "tool_calls", None)
        if tc:
            for c in tc:
                name = c.get("name") if isinstance(c, dict) else getattr(c, "name", None)
                if name:
                    tool_names.append(name)

        name2 = getattr(m, "name", None)
        if name2:
            tool_names.append(name2)

    tool_names = _dedupe_preserve_order(tool_names)
    print("[chat] tools_used =", tool_names if tool_names else "[] (no tool called)")

    if not msgs:
        return "抱歉，我没能理解您的问题。", tokens_used

    last_msg = msgs[-1]
    response_text = getattr(last_msg, "content", None) or str(last_msg)

    quality = compute_quality_flags(response_text, source_count)
    logger.info(json.dumps({"event": "quality_flag", **quality}))

    return response_text, tokens_used


async def get_chat_response(req: ChatQueryRequest, ctx: ChatQueryContext) -> Tuple[str, int, bool]:
    """
    Returns (answer, tokens_used, ok). ok=False means the query failed
    after its quota slot was already reserved -- callers should refund it.
    """
    try:
        route = route_query(req.user_input)
        print("[chat] route =", route)

        # ---- INVENTORY (DB only) ----
        if route == ROUTE_INVENTORY:
            conn = get_db_con()
            try:
                return handle_inventory(conn, ctx), 0, True
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

        # ---- MANUAL_QA ----
        if route == ROUTE_MANUAL_QA:
            # 先走你现有 deep_agent 流程（下一步我们会把它挪进 manual_qa_handler）
            answer, tokens_used = await handle_manual_qa(req, ctx, _run_deep_agent)
            return answer, tokens_used, True

        # ---- TONE_RECIPE ----
        if route == ROUTE_TONE_RECIPE:
            return await handle_tone_recipe(req, ctx)

        # ---- OTHER (fallback) ----
        # 这里你可以直接 deep_agent，也可以简单闲聊
        if route == ROUTE_OTHER:
            # 在这里手动给 req 注入一个基础指令，防止它完全变成无脑闲聊
            # 这样即使是 OTHER，Agent 发现不会答时也会去调用 search_manual_chunks
            req.user_input = f"(Technical Context: User is using {ctx.active_device.model}) {req.user_input}"
            answer, tokens_used = await _run_deep_agent(req, ctx)
            return answer, tokens_used, True
        # return await _run_deep_agent(req, ctx)

    except Exception as e:
        print(f"Chat Service Error: {str(e)}")
        return f"对话服务出现异常: {str(e)}", 0, False
