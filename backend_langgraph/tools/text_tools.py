# Text processing tools for LangGraph

from typing import Dict, Any
from utils.logging_config import logger

def summarize_text(state: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize text content."""
    
    try:
        user_input = state.get("user_input", "")
        
        # Extract text to summarize (simplified)
        # In practice, you'd use LLM to extract the text content
        text_to_summarize = user_input
        
        # Simple summarization (replace with LLM-based summarization)
        words = text_to_summarize.split()
        if len(words) > 50:
            # Take first 50 words as summary
            summary = " ".join(words[:50]) + "..."
        else:
            summary = text_to_summarize
        
        # Add tool result to state
        tool_results = state.get("tool_results", [])
        tool_results.append({
            "tool": "summarize_text",
            "output": f"Summary: {summary}"
        })
        state["tool_results"] = tool_results
        
        logger.info("Text summarization completed")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in text summarization: {str(e)}")
        state["error_message"] = f"Error in text summarization: {str(e)}"
        state["has_error"] = True
        return state

def query_database(state: Dict[str, Any]) -> Dict[str, Any]:
    """Query database for information."""
    
    try:
        user_input = state.get("user_input", "")
        
        # Simple database query simulation
        # In practice, you'd connect to actual database
        query_result = f"Database query for '{user_input}' returned sample results."
        
        # Add tool result to state
        tool_results = state.get("tool_results", [])
        tool_results.append({
            "tool": "query_database",
            "output": query_result
        })
        state["tool_results"] = tool_results
        
        logger.info("Database query completed")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in database query: {str(e)}")
        state["error_message"] = f"Error in database query: {str(e)}"
        state["has_error"] = True
        return state 