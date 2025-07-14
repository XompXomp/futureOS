import json
import os
from typing import Dict, Any
from utils.logging_config import logger
from config.settings import settings

def read_json_file(state: Dict[str, Any]) -> Dict[str, Any]:
    """Read JSON file from specified path."""
    try:
        file_path = state.get("file_path", "")
        if not file_path:
            # Default to data/docs directory
            file_path = "data/docs/patient_profile.json"
        
        # If only filename is provided, prepend data/docs directory
        if not os.path.dirname(file_path):
            file_path = os.path.join("data/docs", file_path)
        
        if not os.path.exists(file_path):
            state["error_message"] = f"File not found: {file_path}"
            state["has_error"] = True
            return state
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        tool_results = state.get("tool_results", [])
        tool_results.append({
            "tool": "read_json_file",
            "output": f"Successfully read JSON file: {file_path}",
            "data": data
        })
        state["tool_results"] = tool_results
        state["json_data"] = data
        
        logger.info(f"JSON file read successfully: {file_path}")
        return state
        
    except Exception as e:
        logger.error(f"Error reading JSON file: {str(e)}")
        state["error_message"] = f"Error reading JSON file: {str(e)}"
        state["has_error"] = True
        return state

def write_json_file(state: Dict[str, Any]) -> Dict[str, Any]:
    """Write data to JSON file."""
    try:
        file_path = state.get("file_path", "")
        data = state.get("data", {})
        
        if not file_path:
            # Default to data/docs directory
            file_path = "data/docs/new_file.json"
        
        # If only filename is provided, prepend data/docs directory
        if not os.path.dirname(file_path):
            file_path = os.path.join("data/docs", file_path)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        tool_results = state.get("tool_results", [])
        tool_results.append({
            "tool": "write_json_file",
            "output": f"Successfully wrote JSON file: {file_path}"
        })
        state["tool_results"] = tool_results
        
        logger.info(f"JSON file written successfully: {file_path}")
        return state
        
    except Exception as e:
        logger.error(f"Error writing JSON file: {str(e)}")
        state["error_message"] = f"Error writing JSON file: {str(e)}"
        state["has_error"] = True
        return state

def list_json_files(state: Dict[str, Any]) -> Dict[str, Any]:
    """List JSON files in a directory."""
    try:
        directory = state.get("directory", "data/docs")
        
        if not os.path.exists(directory):
            state["error_message"] = f"Directory not found: {directory}"
            state["has_error"] = True
            return state
        
        json_files = []
        for file in os.listdir(directory):
            if file.endswith('.json'):
                json_files.append(file)
        
        tool_results = state.get("tool_results", [])
        tool_results.append({
            "tool": "list_json_files",
            "output": f"Found {len(json_files)} JSON files in {directory}",
            "files": json_files
        })
        state["tool_results"] = tool_results
        state["json_files"] = json_files
        
        logger.info(f"Listed JSON files in {directory}: {json_files}")
        return state
        
    except Exception as e:
        logger.error(f"Error listing JSON files: {str(e)}")
        state["error_message"] = f"Error listing JSON files: {str(e)}"
        state["has_error"] = True
        return state 