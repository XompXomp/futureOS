# JSON manipulation tools 

from langchain.agents import Tool
from modules.json_operations import JSONOperations
from config.settings import settings
from utils.logging_config import logger

def create_json_tools():
    """Create JSON operation tools for the agent."""
    
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
        """Read patient profile information."""
        try:
            profile_data = JSONOperations.load_json_from_file(settings.PATIENT_PROFILE_PATH)
            if profile_data is None:
                return "Error: Could not read patient profile"
            
            if query:
                # Filter based on query
                relevant_info = {}
                query_lower = query.lower()
                for key, value in profile_data.items():
                    if query_lower in key.lower() or query_lower in str(value).lower():
                        relevant_info[key] = value
                
                if relevant_info:
                    return f"Found relevant information: {relevant_info}"
                else:
                    return f"No information found for query: {query}"
            else:
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
            description="Read patient profile information. Use this when the user asks about their personal or medical information. After getting the information, provide a direct answer to the user. Optional input: specific field to query (e.g., 'age', 'medications')"
        )
    ]