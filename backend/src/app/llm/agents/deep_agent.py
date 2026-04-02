# app/llm/agents/deep_agent.py
from typing import Any, List, Optional
import json

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable

from langgraph.prebuilt import create_react_agent
from app.llm.guitar_fx_agent.config import get_llm

SYSTEM_PROMPT = """
You are GuitarFX-Agent, a professional assistant helping guitarists configure pedals.

IMPORTANT TOOL RULES (strict):
- When the user asks about manuals / device features, you MUST use tools (especially search_manual_chunks) first.
- You may ONLY answer using information that appears in the tool results. Do NOT speculate or infer missing features.
- If tool results contain the phrase "FX LOOP" (case-insensitive), you MUST quote verbatim the exact sentence that contains "FX LOOP".
- You MUST NOT say "the manual doesn't mention FX LOOP" if that phrase appears in the tool results.
- Do NOT claim the device lacks send/return, lacks 4-cable method, etc., unless the tool results explicitly state that.

Language:
- Respond in Chinese or English matching the user's language.
""".strip()



def _fix_tool_calls_in_ai_message(msg: Any) -> Any:
    """Ensure AIMessage.tool_calls[*].args is a dict (not a JSON string)."""
    if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
        fixed = []
        for tc in msg.tool_calls:
            args = tc.get("args")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}
            if not isinstance(args, dict):
                args = {}
            fixed.append({**tc, "args": args})
        return msg.model_copy(update={"tool_calls": fixed})
    return msg


class ToolCallArgsFixingRunnable(Runnable):
    """
    Runnable wrapper around a chat model that:
    - preserves bind_tools() (create_react_agent uses it)
    - fixes tool_calls args after model output
    """

    def __init__(self, base: Any):
        self.base = base

    def bind_tools(self, tools: Any, **kwargs: Any) -> "ToolCallArgsFixingRunnable":
        # delegate to underlying model, then wrap again
        bound = self.base.bind_tools(tools, **kwargs)
        return ToolCallArgsFixingRunnable(bound)

    def invoke(self, input: Any, config: Optional[dict] = None, **kwargs: Any) -> Any:
        out = self.base.invoke(input, config=config, **kwargs)
        return _fix_tool_calls_in_ai_message(out)

    async def ainvoke(self, input: Any, config: Optional[dict] = None, **kwargs: Any) -> Any:
        out = await self.base.ainvoke(input, config=config, **kwargs)
        return _fix_tool_calls_in_ai_message(out)

    # delegate anything else (streaming etc.)
    def __getattr__(self, name: str) -> Any:
        return getattr(self.base, name)


def build_deep_agent(tools: List[Any]):
    base_model = get_llm()
    model = ToolCallArgsFixingRunnable(base_model)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ])
    return create_react_agent(model=model, tools=tools, prompt=prompt)
