from typing import Any, Dict, List
from langchain_core.runnables import Runnable

PHYSICS_CONTEXT = (
    "You are assisting a graduate student working on lattice models and "
    "variational Monte Carlo (VMC), including 2D Hubbard and TFIM, ground-state "
    "energies, variances, and Transformer-based wavefunction models."
)


def physics_context_middleware(next: Runnable) -> Runnable:
    async def _ainvoke(input: Dict[str, Any], config=None) -> Any:
        messages: List[Dict[str, Any]] = input.get("messages", [])
        new_messages = [
            {"role": "system", "content": PHYSICS_CONTEXT},
            *messages,
        ]
        new_input = {**input, "messages": new_messages}
        return await next.ainvoke(new_input, config=config)

    class Wrapped(Runnable):
        async def ainvoke(self, i, config=None):
            return await _ainvoke(i, config)

        def invoke(self, i, config=None):
            import asyncio
            return asyncio.run(self.ainvoke(i, config))

    return Wrapped()
