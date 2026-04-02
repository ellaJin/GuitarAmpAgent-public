from typing import Any, Dict
from langchain_core.runnables import Runnable


def logging_middleware(next: Runnable) -> Runnable:
    async def _ainvoke(input: Dict[str, Any], config=None) -> Any:
        print("\n====== [LoggingMW] Input ======")
        print(input)
        result = await next.ainvoke(input, config=config)
        print("====== [LoggingMW] Output ======")
        print(result)
        return result

    class Wrapped(Runnable):
        async def ainvoke(self, i, config=None):
            return await _ainvoke(i, config)

        def invoke(self, i, config=None):
            import asyncio
            return asyncio.run(self.ainvoke(i, config))

    return Wrapped()
