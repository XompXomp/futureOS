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
            description="Search the web for current information. Input: state dict."
        )
    ] 