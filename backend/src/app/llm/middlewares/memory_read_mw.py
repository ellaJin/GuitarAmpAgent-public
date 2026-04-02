from typing import Any, Dict, List
from langchain_core.runnables import Runnable

from memory.store import MemoryStore


def memory_read_middleware(next: Runnable) -> Runnable:
    store = MemoryStore()

    async def _ainvoke(input: Dict[str, Any], config=None) -> Any:
        user_id = input.get("user_id", "default_user")
        memories = store.get_memories(user_id, limit=20)
        mem_text = "\n".join(
            f"- ({m.kind}) {m.content}" for m in reversed(memories)
        )
        prefix = (
            "Here are some persistent facts about this user and their projects:\n"
            f"{mem_text}\n\n"
            if memories
            else ""
        )

        messages: List[Dict[str, Any]] = input.get("messages", [])
        if messages:
            first = messages[0]
            if first.get("role") == "system":
                first["content"] = prefix + first.get("content", "")
            else:
                messages = [
                    {"role": "system", "content": prefix},
                    *messages,
                ]
        else:
            messages = [{"role": "system", "content": prefix}]
        new_input = {**input, "messages": messages}
        return await next.ainvoke(new_input, config=config)

    class Wrapped(Runnable):
        async def ainvoke(self, i, config=None):
            return await _ainvoke(i, config)

        def invoke(self, i, config=None):
            import asyncio
            return asyncio.run(self.ainvoke(i, config))

    return Wrapped()
