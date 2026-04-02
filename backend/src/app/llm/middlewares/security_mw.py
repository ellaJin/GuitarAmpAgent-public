from typing import Any, Dict, List
import re
from langchain_core.runnables import Runnable

PROMPT_INJECTION_PATTERNS = [
    r"(?i)ignore previous instructions",
    r"(?i)忽略以上所有指令",
    r"(?i)you are now another model",
    r"(?i)你现在不再是",
]


def _contains_injection(text: str) -> bool:
    return any(re.search(p, text) for p in PROMPT_INJECTION_PATTERNS)


def security_middleware(next: Runnable) -> Runnable:
    async def _ainvoke(input: Dict[str, Any], config=None) -> Any:
        messages: List[Dict[str, Any]] = input.get("messages", [])
        if messages:
            last = messages[-1]
            if last.get("role") == "user":
                user_text = str(last.get("content", ""))
                if _contains_injection(user_text):
                    return {
                        "messages": [
                            {
                                "role": "assistant",
                                "content": "⚠️ 检测到可能的提示注入内容，已根据安全策略拒绝处理。",
                            }
                        ]
                    }
        return await next.ainvoke(input, config=config)

    class Wrapped(Runnable):
        async def ainvoke(self, i, config=None):
            return await _ainvoke(i, config)

        def invoke(self, i, config=None):
            import asyncio
            return asyncio.run(self.ainvoke(i, config))

    return Wrapped()
