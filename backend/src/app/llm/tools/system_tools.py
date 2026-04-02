from langchain_core.tools import tool


@tool
def echo_tool(text: str) -> str:
    """
    Simple debug tool: echoes back the text.
    Useful to test tool calling behavior.
    """
    return f"[echo] {text}"
