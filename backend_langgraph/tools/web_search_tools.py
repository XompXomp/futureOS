# Web search tools for LangGraph

import requests
from typing import Dict, Any
from utils.logging_config import logger
from config.settings import settings

def search_web(state: Dict[str, Any]) -> Dict[str, Any]:
    """Search the web using Google Programmable Search Engine."""
    
    try:
        user_input = state.get("user_input", "")
        
        if not settings.GOOGLE_PSE_API_KEY or not settings.GOOGLE_PSE_CX:
            raise ValueError("Google PSE API key or CX not configured")
        
        # Build search query
        search_query = user_input
        
        # Make API request
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': settings.GOOGLE_PSE_API_KEY,
            'cx': settings.GOOGLE_PSE_CX,
            'q': search_query,
            'num': 5  # Number of results
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract search results
        search_results = []
        if 'items' in data:
            for item in data['items']:
                result = {
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', '')
                }
                search_results.append(result)
        
        # Format results for output
        if search_results:
            output = f"Found {len(search_results)} search results for '{search_query}':\n\n"
            for i, result in enumerate(search_results, 1):
                output += f"{i}. {result['title']}\n"
                output += f"   {result['link']}\n"
                output += f"   {result['snippet']}\n\n"
        else:
            output = f"No search results found for '{search_query}'"
        
        # Add tool result to state
        tool_results = state.get("tool_results", [])
        tool_results.append({
            "tool": "search_web",
            "output": output
        })
        state["tool_results"] = tool_results
        
        logger.info(f"Web search completed for: {search_query}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in web search: {str(e)}")
        state["error_message"] = f"Error in web search: {str(e)}"
        state["has_error"] = True
        return state 