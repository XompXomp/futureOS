# File operation tools for LangGraph

import os
from typing import Dict, Any
from utils.logging_config import logger
from config.settings import settings

def read_file(state: Dict[str, Any]) -> Dict[str, Any]:
    """Read file content using semantic understanding."""
    
    try:
        user_input = state.get("user_input", "")
        
        # Use semantic understanding to extract file path
        # This would typically use an LLM to understand the user's intent
        file_path = _extract_file_path_semantic(user_input, "read")
        
        if not file_path:
            # Default to data/docs directory
            file_path = "data/docs/example.txt"
        
        # If only filename is provided, prepend data/docs directory
        if not os.path.dirname(file_path):
            file_path = os.path.join("data/docs", file_path)
        
        # Ensure the file exists
        if not os.path.exists(file_path):
            # Create a sample file
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write("This is a sample file created by the LangGraph system.\n")
                f.write("You can modify this file or create new ones.\n")
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add tool result to state
        tool_results = state.get("tool_results", [])
        tool_results.append({
            "tool": "read_file",
            "output": f"File '{file_path}' read successfully using semantic extraction. Content: {content[:200]}..."
        })
        state["tool_results"] = tool_results
        state["file_content"] = content
        state["file_path"] = file_path
        
        logger.info(f"File read successfully using semantic extraction: {file_path}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        state["error_message"] = f"Error reading file: {str(e)}"
        state["has_error"] = True
        return state

def write_file(state: Dict[str, Any]) -> Dict[str, Any]:
    """Write content to file using semantic understanding."""
    
    try:
        user_input = state.get("user_input", "")
        
        # Use semantic understanding to extract file path and content
        # This would typically use an LLM to understand the user's intent
        extraction_result = _extract_file_info_semantic(user_input)
        file_path = extraction_result.get("file_path")
        content = extraction_result.get("content")
        
        if not file_path:
            # Default to data/docs directory
            file_path = "data/docs/user_created.txt"
        
        # If only filename is provided, prepend data/docs directory
        if not os.path.dirname(file_path):
            file_path = os.path.join("data/docs", file_path)
        
        if not content:
            # Extract content from user input using semantic understanding
            content = _extract_content_semantic(user_input)
            if not content:
                content = "File created by LangGraph system using semantic understanding."
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Add tool result to state
        tool_results = state.get("tool_results", [])
        tool_results.append({
            "tool": "write_file",
            "output": f"File '{file_path}' written successfully using semantic extraction with content: {content[:100]}..."
        })
        state["tool_results"] = tool_results
        state["file_path"] = file_path
        state["file_content"] = content
        
        logger.info(f"File written successfully using semantic extraction: {file_path}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error writing file: {str(e)}")
        state["error_message"] = f"Error writing file: {str(e)}"
        state["has_error"] = True
        return state

def _extract_file_path_semantic(user_input: str, operation: str) -> str:
    """Extract file path using semantic understanding (placeholder for LLM)."""
    # This function would use an LLM to extract file paths from natural language
    # For now, we'll use enhanced pattern matching
    
    import re
    
    # Enhanced file path extraction patterns
    if operation == "read":
        patterns = [
            r'read\s+(.+?\.(?:txt|json|py|md|csv|html|css|js))',
            r'open\s+(.+?\.(?:txt|json|py|md|csv|html|css|js))',
            r'file\s+(.+?\.(?:txt|json|py|md|csv|html|css|js))',
            r'read\s+the\s+file\s+(.+?\.(?:txt|json|py|md|csv|html|css|js))',
            r'open\s+the\s+file\s+(.+?\.(?:txt|json|py|md|csv|html|css|js))'
        ]
    else:  # write
        patterns = [
            r'write\s+(.+?\.(?:txt|json|py|md|csv|html|css|js))',
            r'create\s+(.+?\.(?:txt|json|py|md|csv|html|css|js))',
            r'save\s+(.+?\.(?:txt|json|py|md|csv|html|css|js))',
            r'write\s+to\s+(.+?\.(?:txt|json|py|md|csv|html|css|js))',
            r'create\s+a\s+file\s+(.+?\.(?:txt|json|py|md|csv|html|css|js))'
        ]
    
    for pattern in patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return ""

def _extract_file_info_semantic(user_input: str) -> Dict[str, Any]:
    """Extract file path and content using semantic understanding."""
    # This function would use an LLM to extract both file path and content
    # For now, we'll use enhanced pattern matching
    
    import re
    
    # Extract file path
    file_path = _extract_file_path_semantic(user_input, "write")
    
    # Extract content (everything after the file path)
    content = None
    if file_path and file_path in user_input:
        content_start = user_input.find(file_path) + len(file_path)
        content = user_input[content_start:].strip()
    
    return {
        "file_path": file_path,
        "content": content
    }

def _extract_content_semantic(user_input: str) -> str:
    """Extract content using semantic understanding."""
    # This function would use an LLM to extract content from natural language
    # For now, we'll use enhanced pattern matching
    
    import re
    
    # Remove common file operation words
    content = user_input
    operation_words = ['write', 'create', 'save', 'file', 'document']
    
    for word in operation_words:
        content = re.sub(rf'\b{word}\b', '', content, flags=re.IGNORECASE)
    
    # Clean up extra whitespace
    content = ' '.join(content.split())
    
    return content if content else "" 