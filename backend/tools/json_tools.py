# JSON manipulation tools 

from langchain.agents import Tool
from modules.json_operations import JSONOperations
from config.settings import settings
from utils.logging_config import logger
from tools.rag_tools import create_rag_tools

def create_json_tools():
    """Create JSON operation tools for the agent."""
    
    rag_tools = create_rag_tools()
    ask_documents_tool = None
    for tool in rag_tools:
        if tool.name == "ask_documents":
            ask_documents_tool = tool.func
            break

    def update_patient_profile_tool(user_input: str) -> str:
        """Update patient profile based on natural language input."""
        try:
            # Extract updates from natural language
            updates = JSONOperations.extract_json_updates_from_text(user_input)
            
            if not updates:
                return "No recognizable updates found in your input. Please specify what you want to update (e.g., 'My age is 25', 'My name is John', etc.)"
            
            # Update the patient profile
            success = JSONOperations.update_json_values(settings.PATIENT_PROFILE_PATH, updates)
            
            if success:
                updated_fields = ", ".join(updates.keys())
                return f"Successfully updated patient profile fields: {updated_fields}"
            else:
                return "Error: Could not update patient profile"
        except Exception as e:
            return f"Error updating patient profile: {str(e)}"

    def read_patient_profile_tool(query: str = "") -> str:
        """Read patient profile information. Uses RAG for search queries, JSON for full read."""
        try:
            if query:
                # Use RAG for any search/query
                if ask_documents_tool is not None:
                    return ask_documents_tool(query)
                else:
                    return "Error: RAG search tool is not available."
            else:
                # Full read (return the entire JSON)
                profile_data = JSONOperations.load_json_from_file(settings.PATIENT_PROFILE_PATH)
                if profile_data is None:
                    return "Error: Could not read patient profile"
                return f"Full patient profile: {profile_data}"
        except Exception as e:
            return f"Error reading patient profile: {str(e)}"

    return [
        Tool(
            name="update_patient_profile",
            func=update_patient_profile_tool,
            description="Update patient profile information based on natural language input. Example: 'I am 25 years old' or 'My email is john@example.com'"
        ),
        Tool(
            name="read_patient_profile",
            func=read_patient_profile_tool,
            description="Read patient profile information. Uses RAG for search queries, JSON for full read. Optional input: specific field to query (e.g., 'age', 'medications')"
        )
    ]