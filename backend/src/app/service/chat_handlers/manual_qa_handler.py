# app/service/chat_handlers/manual_qa_handler.py
from typing import Callable, Awaitable
from app.schemas.chat import ChatQueryRequest, ChatQueryContext
from app.llm.prompts.manual_qa import (
    ManualQaPromptParams,
    build_manual_qa_system_prompt,
    build_manual_qa_query_extension
)


def _inject_guard_into_req(req: ChatQueryRequest, custom_guard: str) -> ChatQueryRequest:
    """
    修改点：增加 custom_guard 参数，不再使用全局硬编码字符串。
    """

    def _copy(update: dict):
        if hasattr(req, "model_copy"):
            return req.model_copy(update=update)
        if hasattr(req, "copy"):
            return req.copy(update=update)
        for k, v in update.items():
            setattr(req, k, v)
        return req

    # 1) messages-based
    if hasattr(req, "messages") and isinstance(getattr(req, "messages"), list):
        msgs = list(getattr(req, "messages"))
        guard_msg = {"role": "system", "content": custom_guard}
        return _copy({"messages": [guard_msg] + msgs})

    # 2) system_prompt field
    if hasattr(req, "system_prompt") and isinstance(getattr(req, "system_prompt"), str):
        old = getattr(req, "system_prompt") or ""
        merged = (custom_guard + "\n\n" + old).strip()
        return _copy({"system_prompt": merged})

    # 3) prompt field
    if hasattr(req, "prompt") and isinstance(getattr(req, "prompt"), str):
        old = getattr(req, "prompt") or ""
        merged = (custom_guard + "\n\n" + old).strip()
        return _copy({"prompt": merged})

    # 4) query/text field (fallback)
    for key in ("query", "text", "question", "input"):
        if hasattr(req, key) and isinstance(getattr(req, key), str):
            old = getattr(req, key) or ""
            merged = f"{custom_guard}\n\nUser question:\n{old}"
            return _copy({key: merged})

    return req


async def handle_manual_qa(
        req: ChatQueryRequest,
        ctx: ChatQueryContext,
        run_deep_agent: Callable[[ChatQueryRequest, ChatQueryContext], Awaitable[str]],
) -> str:
    # --- 修复点：从 ctx.active_device (ActiveDeviceContext 对象) 中提取字符串 ---
    if ctx.active_device:
        # 按照你定义的 brand + model 组合
        device_name = f"{ctx.active_device.brand} {ctx.active_device.model}"
    else:
        device_name = "Guitar Effects Device"

    user_name = ctx.user_name

    # 1. 自动扩展查询词 (使用组合好的字符串，例如 "Mooer GE150 Pro")
    req.user_input = (
        f"[INSTRUCTION: You MUST use 'search_manual_chunks' to verify the manual's "
        f"exact wording for {device_name} before answering.]\n"
        f"User Question: {req.user_input}"
    )

    # 2. 准备 Prompt 参数
    params = ManualQaPromptParams(
        device_name=device_name,
        user_name=user_name
    )

    # 3. 生成动态 Guard 提示词
    dynamic_guard = build_manual_qa_system_prompt(params)

    # 4. 注入并运行
    req2 = _inject_guard_into_req(req, dynamic_guard)

    return await run_deep_agent(req2, ctx)