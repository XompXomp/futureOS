# Patient profile tools for LangGraph

import json
import os
from typing import Dict, Any
from utils.logging_config import logger
from config.settings import settings

def read_patient_profile(state: Dict[str, Any]) -> Dict[str, Any]:
    """Read patient profile from JSON file."""
    
    try:
        profile_path = settings.PATIENT_PROFILE_PATH
        
        if not os.path.exists(profile_path):
            # Create default profile
            default_profile = {
                "personal_info": {
                    "name": "",
                    "age": 0,
                    "gender": "",
                    "phone": "",
                    "email": "",
                    "address": ""
                },
                "medical_info": {
                    "height": 0,
                    "weight": 0,
                    "blood_type": "",
                    "allergies": [],
                    "chronic_conditions": [],
                    "current_medications": []
                },
                "emergency_contact": {
                    "name": "",
                    "relationship": "",
                    "phone": ""
                },
                "insurance": {
                    "provider": "",
                    "policy_number": "",
                    "group_number": ""
                }
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(profile_path), exist_ok=True)
            
            with open(profile_path, 'w') as f:
                json.dump(default_profile, f, indent=2)
            
            profile_data = default_profile
            logger.info("Created default patient profile")
        else:
            with open(profile_path, 'r') as f:
                profile_data = json.load(f)
            logger.info("Loaded existing patient profile")
        
        # Add tool result to state
        tool_results = state.get("tool_results", [])
        tool_results.append({
            "tool": "read_patient_profile",
            "output": f"Patient profile loaded successfully. Profile contains: {list(profile_data.keys())}"
        })
        state["tool_results"] = tool_results
        state["patient_profile"] = profile_data
        
        return state
        
    except Exception as e:
        logger.error(f"Error reading patient profile: {str(e)}")
        state["error_message"] = f"Error reading patient profile: {str(e)}"
        state["has_error"] = True
        return state

def update_patient_profile(state: Dict[str, Any]) -> Dict[str, Any]:
    """Update patient profile using LLM to extract information from natural language."""
    
    try:
        user_input = state.get("user_input", "")
        current_profile = state.get("patient_profile", {})
        
        if not current_profile:
            # Load current profile first
            state = read_patient_profile(state)
            current_profile = state.get("patient_profile", {})
        
        # Create update prompt for LLM
        update_prompt = f"""You are updating a patient profile. Extract relevant information from the user's input and update the JSON profile accordingly.

                        Current Profile:
                        {json.dumps(current_profile, indent=2)}

                        User Input: {user_input}

                        Update the profile with the new information from the user's input. Return only the updated JSON profile.
                        Maintain the existing structure and only update the fields that are mentioned in the user input.
                        """

        # For now, use simple pattern matching (can be replaced with LLM call)
        # This is a simplified version - in practice, you'd use an LLM to parse the input
        
        updated_profile = current_profile.copy()
        
        # Simple keyword-based updates (replace with LLM parsing)
        user_input_lower = user_input.lower()
        
        if "name" in user_input_lower:
            # Extract name (simplified)
            words = user_input.split()
            for i, word in enumerate(words):
                if word.lower() in ["name", "called", "is"] and i + 1 < len(words):
                    updated_profile["personal_info"]["name"] = words[i + 1]
                    break
        
        if "age" in user_input_lower:
            # Extract age (simplified)
            import re
            age_match = re.search(r'(\d+)', user_input)
            if age_match:
                updated_profile["personal_info"]["age"] = int(age_match.group(1))
        
        # Save updated profile
        profile_path = settings.PATIENT_PROFILE_PATH
        with open(profile_path, 'w') as f:
            json.dump(updated_profile, f, indent=2)
        
        # Add tool result to state
        tool_results = state.get("tool_results", [])
        tool_results.append({
            "tool": "update_patient_profile",
            "output": f"Patient profile updated successfully. Changes made based on: {user_input[:50]}..."
        })
        state["tool_results"] = tool_results
        state["patient_profile"] = updated_profile
        state["profile_updated"] = True
        
        logger.info("Patient profile updated successfully")
        
        return state
        
    except Exception as e:
        logger.error(f"Error updating patient profile: {str(e)}")
        state["error_message"] = f"Error updating patient profile: {str(e)}"
        state["has_error"] = True
        return state 