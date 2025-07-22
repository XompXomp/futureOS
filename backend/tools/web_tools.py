# Google PSE search tools

from langchain.agents import Tool
from modules.web_operations import WebOperations

def create_web_tools():
    def web_search_tool(state: dict) -> dict:
        result = WebOperations.search_web(state)
        state['results'] = result.get('results', result.get('error', 'No results found.'))
        return state
    return [
        Tool(
            name="web_search",
            func=web_search_tool,
            description=(
                "Use this tool to search the web for up-to-date, factual, or real-time information that "
                "cannot be reliably answered from static memory or internal knowledge. "
                "This includes topics such as:\n"
                "- Current stock prices (e.g., 'Nvidia stock price')\n"
                "- Latest news (e.g., 'earthquake in Japan today')\n"
                "- Cryptocurrency values (e.g., 'Bitcoin price now')\n"
                "- Weather forecasts (e.g., 'weather in Dubai tomorrow')\n"
                "- Sports scores (e.g., 'Manchester United last match score')\n"
                "- Public statistics that may change (e.g., 'current population of China', 'latest COVID cases in US')\n\n"
                "DO NOT use this for static factual questions like: 'Who is the president of India?' or 'What is the capital of France?' "
                "unless specifically asked for 'current', 'latest', or 'today'."
            )
        )
    ] 