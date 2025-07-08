# File operation tools 

from langchain.agents import Tool
from modules.file_operations import FileOperations
from utils.logging_config import logger

def create_file_tools():
    """Create file operation tools for the agent."""
    
    def read_file_tool(file_path: str) -> str:
        """Read content from a file."""
        try:
            content = FileOperations.read_file(file_path)
            if content is None:
                return f"Error: Could not read file {file_path}"
            return f"File content from {file_path}:\n{content}"
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def write_file_tool(input_str: str) -> str:
        """Write content to a file. Format: 'file_path|content'"""
        try:
            parts = input_str.split('|', 1)
            if len(parts) != 2:
                return "Error: Please provide input in format 'file_path|content'"
            
            file_path, content = parts
            success = FileOperations.write_file(file_path.strip(), content.strip())
            if success:
                return f"Successfully wrote content to {file_path}"
            else:
                return f"Error: Could not write to file {file_path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def append_file_tool(input_str: str) -> str:
        """Append content to a file. Format: 'file_path|content'"""
        try:
            parts = input_str.split('|', 1)
            if len(parts) != 2:
                return "Error: Please provide input in format 'file_path|content'"
            
            file_path, content = parts
            success = FileOperations.append_to_file(file_path.strip(), content.strip())
            if success:
                return f"Successfully appended content to {file_path}"
            else:
                return f"Error: Could not append to file {file_path}"
        except Exception as e:
            return f"Error appending to file: {str(e)}"

    return [
        Tool(
            name="read_file",
            func=read_file_tool,
            description="Read content from a text file. Input: file_path"
        ),
        Tool(
            name="write_file",
            func=write_file_tool,
            description="Write content to a text file. Input: 'file_path|content'"
        ),
        Tool(
            name="append_file",
            func=append_file_tool,
            description="Append content to a text file. Input: 'file_path|content'"
        )
    ]