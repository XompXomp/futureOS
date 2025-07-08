# Google PSE search tools

from langchain.agents import Tool
from modules.google_pse_search import GooglePSESearch
from utils.logging_config import logger

def create_google_pse_tools():
    """Create Google PSE search tools for the agent."""
    
    google_pse = GooglePSESearch()
    
    def web_search_tool(query: str) -> str:
        """Search the web using Google PSE."""
        try:
            if not query or query.strip() == "":
                return "Error: Please provide a search query"
            
            results = google_pse.search(query, num_results=5)
            
            if not results:
                return "No search results found for your query."
            
            formatted_results = "Web Search Results:\n\n"
            for i, result in enumerate(results, 1):
                formatted_results += f"{i}. {result['title']}\n"
                formatted_results += f"   URL: {result['link']}\n"
                formatted_results += f"   Snippet: {result['snippet']}\n\n"
            
            return formatted_results
        except Exception as e:
            return f"Error performing web search: {str(e)}"
    
    def search_documents_tool(query: str) -> str:
        """Search and return documents in a format suitable for further processing."""
        try:
            if not query or query.strip() == "":
                return "Error: Please provide a search query"
            
            documents = google_pse.search_documents(query, num_results=5)
            
            if not documents:
                return "No search results found for your query."
            
            formatted_results = "Search Documents:\n\n"
            for i, doc in enumerate(documents, 1):
                formatted_results += f"Document {i}:\n{doc['page_content']}\n\n"
            
            return formatted_results
        except Exception as e:
            return f"Error searching documents: {str(e)}"
    
    return [
        Tool(
            name="web_search",
            func=web_search_tool,
            description="Search the web for current information. Input: your search query"
        ),
        Tool(
            name="search_documents",
            func=search_documents_tool,
            description="Search the web and return results in document format for further processing. Input: your search query"
        )
    ] 