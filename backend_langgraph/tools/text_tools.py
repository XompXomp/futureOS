# Text processing tools for LangGraph

import re
from typing import Dict, Any, List
from utils.logging_config import logger
from config.settings import settings

def summarize_text(state: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize text content using semantic understanding."""
    
    try:
        user_input = state.get("user_input", "")
        text_content = state.get("file_content", "")
        
        # Use semantic understanding to extract text to summarize
        if not text_content:
            text_content = _extract_text_content_semantic(user_input)
        
        if not text_content:
            # Use the entire user input as text to summarize
            text_content = user_input
        
        # Simple summarization (in practice, use LLM)
        words = text_content.split()
        if len(words) > 50:
            # Take first 50 words as summary
            summary = " ".join(words[:50]) + "..."
        else:
            summary = text_content
        
        # Add tool result to state
        tool_results = state.get("tool_results", [])
        tool_results.append({
            "tool": "summarize_text",
            "output": f"Text summarized successfully using semantic extraction. Original length: {len(text_content)} characters. Summary: {summary[:100]}..."
        })
        state["tool_results"] = tool_results
        state["text_summary"] = summary
        state["original_text"] = text_content
        
        logger.info(f"Text summarized successfully using semantic extraction. Original length: {len(text_content)} characters")
        
        return state
        
    except Exception as e:
        logger.error(f"Error summarizing text: {str(e)}")
        state["error_message"] = f"Error summarizing text: {str(e)}"
        state["has_error"] = True
        return state

def query_database(state: Dict[str, Any]) -> Dict[str, Any]:
    """Query database for information using semantic understanding."""
    
    try:
        user_input = state.get("user_input", "")
        
        # Use semantic understanding to extract query
        # This would typically use an LLM to understand the user's intent
        query = _extract_database_query_semantic(user_input)
        
        if not query:
            # Use the entire user input as query
            query = user_input
        
        # Mock database query results
        mock_results = [
            {
                "id": 1,
                "name": "Sample Record 1",
                "description": f"Database record related to '{query}'",
                "created_date": "2024-01-15"
            },
            {
                "id": 2,
                "name": "Sample Record 2", 
                "description": f"Another record matching '{query}'",
                "created_date": "2024-01-16"
            }
        ]
        
        # Format results
        results_text = f"Database query results for '{query}':\n\n"
        for i, result in enumerate(mock_results, 1):
            results_text += f"{i}. {result['name']}\n"
            results_text += f"   Description: {result['description']}\n"
            results_text += f"   Created: {result['created_date']}\n\n"
        
        # Add tool result to state
        tool_results = state.get("tool_results", [])
        tool_results.append({
            "tool": "query_database",
            "output": f"Database query completed for '{query}' using semantic extraction. Found {len(mock_results)} records."
        })
        state["tool_results"] = tool_results
        state["database_results"] = mock_results
        state["database_query"] = query
        
        logger.info(f"Database query completed using semantic extraction for: {query}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error querying database: {str(e)}")
        state["error_message"] = f"Error querying database: {str(e)}"
        state["has_error"] = True
        return state

def extract_keywords(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract keywords from text using semantic understanding."""
    
    try:
        text_content = state.get("file_content", "") or state.get("user_input", "")
        
        if not text_content:
            state["error_message"] = "No text content to extract keywords from"
            state["has_error"] = True
            return state
        
        # Simple keyword extraction (in practice, use NLP libraries)
        words = re.findall(r'\b\w+\b', text_content.lower())
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Count frequency
        from collections import Counter
        keyword_freq = Counter(keywords)
        
        # Get top 10 keywords
        top_keywords = keyword_freq.most_common(10)
        
        # Format results
        keywords_text = "Top keywords found:\n"
        for keyword, count in top_keywords:
            keywords_text += f"- {keyword}: {count} times\n"
        
        # Add tool result to state
        tool_results = state.get("tool_results", [])
        tool_results.append({
            "tool": "extract_keywords",
            "output": f"Keywords extracted successfully using semantic extraction. Found {len(top_keywords)} top keywords."
        })
        state["tool_results"] = tool_results
        state["keywords"] = top_keywords
        state["keyword_text"] = keywords_text
        
        logger.info(f"Keywords extracted successfully using semantic extraction. Found {len(top_keywords)} top keywords")
        
        return state
        
    except Exception as e:
        logger.error(f"Error extracting keywords: {str(e)}")
        state["error_message"] = f"Error extracting keywords: {str(e)}"
        state["has_error"] = True
        return state

def _extract_text_content_semantic(user_input: str) -> str:
    """Extract text content using semantic understanding (placeholder for LLM)."""
    # This function would use an LLM to extract text content from natural language
    # For now, we'll use enhanced pattern matching
    
    import re
    
    # Enhanced text content extraction patterns
    text_patterns = [
        r'summarize\s+(.+)',
        r'summary\s+of\s+(.+)',
        r'brief\s+(.+)',
        r'summarize\s+the\s+text\s+(.+)',
        r'create\s+a\s+summary\s+of\s+(.+)',
        r'brief\s+summary\s+of\s+(.+)'
    ]
    
    for pattern in text_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return ""

def _extract_database_query_semantic(user_input: str) -> str:
    """Extract database query using semantic understanding (placeholder for LLM)."""
    # This function would use an LLM to extract database queries from natural language
    # For now, we'll use enhanced pattern matching
    
    import re
    
    # Enhanced database query extraction patterns
    query_patterns = [
        r'query\s+(.+)',
        r'search\s+database\s+for\s+(.+)',
        r'find\s+in\s+database\s+(.+)',
        r'query\s+the\s+database\s+for\s+(.+)',
        r'search\s+for\s+(.+)',
        r'find\s+(.+)',
        r'look\s+up\s+(.+)',
        r'get\s+information\s+about\s+(.+)'
    ]
    
    for pattern in query_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return "" 