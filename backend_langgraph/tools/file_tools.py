# File operation tools for LangGraph

import os
from typing import Dict, Any
from utils.logging_config import logger
from config.settings import settings

def read_file(state: Dict[str, Any]) -> Dict[str, Any]:
    """Read file content."""
    
    try:
        user_input = state.get("user_input", "")
        
        # Extract filename from user input (simplified)
        # In practice, you'd use LLM to extract the filename
        words = user_input.split()
        filename = None
        
        for word in words:
            if word.endswith(('.txt', '.json', '.md', '.py', '.html', '.css', '.js')):
                filename = word
                break
        
        if not filename:
            # Default to patient profile
            filename = settings.PATIENT_PROFILE_PATH
        
        # Ensure file exists
        if not os.path.exists(filename):
            # Try relative to docs folder
            docs_filename = os.path.join(settings.DOCS_FOLDER, filename)
            if os.path.exists(docs_filename):
                filename = docs_filename
            else:
                raise FileNotFoundError(f"File not found: {filename}")
        
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add tool result to state
        tool_results = state.get("tool_results", [])
        tool_results.append({
            "tool": "read_file",
            "output": f"File '{filename}' read successfully. Content length: {len(content)} characters."
        })
        state["tool_results"] = tool_results
        
        logger.info(f"Read file: {filename}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        state["error_message"] = f"Error reading file: {str(e)}"
        state["has_error"] = True
        return state

def write_file(state: Dict[str, Any]) -> Dict[str, Any]:
    """Write content to file."""
    
    try:
        user_input = state.get("user_input", "")
        
        # Extract filename and content from user input (simplified)
        # In practice, you'd use LLM to extract filename and content
        words = user_input.split()
        filename = None
        content = ""
        
        # Simple extraction (replace with LLM parsing)
        if "file" in user_input.lower():
            for i, word in enumerate(words):
                if word.lower() == "file" and i + 1 < len(words):
                    filename = words[i + 1]
                    break
        
        if not filename:
            filename = "output.txt"
        
        # Extract content (everything after filename)
        if filename in user_input:
            content_start = user_input.find(filename) + len(filename)
            content = user_input[content_start:].strip()
        
        if not content:
            content = "Default content"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Add tool result to state
        tool_results = state.get("tool_results", [])
        tool_results.append({
            "tool": "write_file",
            "output": f"File '{filename}' written successfully with {len(content)} characters."
        })
        state["tool_results"] = tool_results
        
        logger.info(f"Wrote file: {filename}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error writing file: {str(e)}")
        state["error_message"] = f"Error writing file: {str(e)}"
        state["has_error"] = True
        return state 