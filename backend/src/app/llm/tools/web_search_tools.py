from langchain_core.tools import tool
# from env_utils import SERPAPI_KEY
import requests

@tool("my_web_search", parse_docstring=True)
def web_search(query: str, num_results: int = 5) -> str:
    """
    Perform a web search using SerpAPI and return concise, LLM-friendly results.

    Args:
        query (str): Query string for web search.
        num_results (int): Number of results to return.

    Returns:
        str: A short markdown list of search results (title, short snippet, link).
    """
    try:
        params = {
            "q": query,
            "api_key": "SERPAPI_KEY",
            "engine": "google",
            "num": num_results,
        }
        resp = requests.get("https://serpapi.com/search", params=params)
        data = resp.json()

        results = data.get("organic_results", [])
        if not results:
            return "No results found."

        lines = ["Search results (top {}):".format(min(num_results, len(results)))]
        for i, r in enumerate(results[:num_results], start=1):
            title = r.get("title", "").strip()
            snippet = (r.get("snippet", "") or "").strip()
            link = r.get("link", "").strip()

            # 截断 snippet，避免太长
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."

            lines.append(
                f"{i}. **{title}**\n"
                f"   - Summary: {snippet}\n"
                f"   - Link: {link}"
            )

        # 这个字符串就是传给大模型看的，结构清晰很多
        return "\n".join(lines)

    except Exception as e:
        return f"SerpAPI error: {e}"



# if __name__ == '__main__':
#     print(web_search.name) # tool name
#     print(web_search.description) # tools description
#     print(web_search.args) # tool parameters
#     print(web_search.args_schema.model_json_schema()) # tool parameter's json schema
#
#     results = web_search.invoke({'query':'how to use langchain?'})
#     print(results)
