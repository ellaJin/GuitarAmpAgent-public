from typing import Any, Dict, List
from langchain_core.runnables import Runnable

from memory.store import MemoryStore, MemoryItem


def _extract_memories_from_messages(messages: List[Dict[str, Any]]) -> list[MemoryItem]:
    """
    TODO: implement real heuristic or LLM-based extraction.

    暂时用超简单逻辑：如果用户说了“记住”这个词，就存一条。
    """
    items: list[MemoryItem] = []
    for msg in messages:
        if msg.get("role") == "user":
            content = str(msg.get("content", ""))
            if "记住" in content or "remember" in content.lower():
                items.append(
                    MemoryItem(
                        user_id="default_user",
                        kind="note",
                        content=content,
                    )
                )
    return items


def memory_write_middleware(next: Runnable) -> Runnable:
    store = MemoryStore()

    async def _ainvoke(input: Dict[str, Any], config=None) -> Any:
        result = await next.ainvoke(input, config=config)

        # After agent response, try to extract memories from messages
        messages: List[Dict[str, Any]] = input.get("messages", [])
        new_items = _extract_memories_from_messages(messages)
        for item in new_items:
            store.add_memory(item)

        return result

    class Wrapped(Runnable):
        async def ainvoke(self, i, config=None):
            return await _ainvoke(i, config)

        def invoke(self, i, config=None):
            import asyncio
            return asyncio.run(self.ainvoke(i, config))

    return Wrapped()
