# Patient profile tools for LangGraph

import json
import os
from typing import Dict, Any
from utils.logging_config import logger
from config.settings import settings

# Import LLM (Groq or Ollama)
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


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
            os.makedirs(os.path.dirname(profile_path), exist_ok=True)
            with open(profile_path, 'w') as f:
                json.dump(default_profile, f, indent=2)
            profile_data = default_profile
            logger.info("Created default patient profile")
        else:
            with open(profile_path, 'r') as f:
                profile_data = json.load(f)
            logger.info("Loaded existing patient profile")
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

        # Use LLM to extract and update patient information
        llm = None
        if getattr(settings, "USE_OLLAMA", False):
            llm = ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.3
            )
        else:
            llm = ChatGroq(
                model=settings.LLM_MODEL,
                temperature=0.3
            )

        # Prompt for the LLM
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert medical assistant. Given a user request and the current patient profile (as JSON), extract only the fields that should be updated and return a JSON object with only those fields. Do not return the full profile, only the fields to update. If nothing should be updated, return an empty JSON object.\n\nExample:\nUser: Update my age to 35\nProfile: {\"personal_info\": {\"name\": \"John\", \"age\": 30}}\nOutput: {\"personal_info\": {\"age\": 35}}\n\nUser: My name is Alice and my phone is 123-456-7890\nProfile: {\"personal_info\": {\"name\": \"\", \"phone\": \"\"}}\nOutput: {\"personal_info\": {\"name\": \"Alice\", \"phone\": \"123-456-7890\"}}"),
            ("human", "User: {user_input}\nProfile: {profile}\nOutput:")
        ])
        chain = prompt | llm
        # Run the LLM to get the patch
        patch_json = chain.invoke({
            "user_input": user_input,
            "profile": json.dumps(current_profile)
        })
        # Try to parse the LLM output as JSON
        import re
        import ast
        patch_str = str(patch_json)
        # Extract JSON from the LLM output
        match = re.search(r'\{.*\}', patch_str, re.DOTALL)
        if match:
            patch_obj = match.group(0)
            try:
                patch = json.loads(patch_obj)
            except Exception:
                try:
                    patch = ast.literal_eval(patch_obj)
                except Exception:
                    patch = {}
        else:
            patch = {}
        # Merge the patch into the current profile
        def deep_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict) and isinstance(d.get(k), dict):
                    deep_update(d[k], v)
                else:
                    d[k] = v
        updated_profile = json.loads(json.dumps(current_profile))  # deep copy
        deep_update(updated_profile, patch)
        # Save updated profile
        profile_path = settings.PATIENT_PROFILE_PATH
        with open(profile_path, 'w') as f:
            json.dump(updated_profile, f, indent=2)
        tool_results = state.get("tool_results", [])
        tool_results.append({
            "tool": "update_patient_profile",
            "output": f"Patient profile updated using LLM extraction. Changes: {patch if patch else 'No changes'}"
        })
        state["tool_results"] = tool_results
        state["patient_profile"] = updated_profile
        state["profile_updated"] = bool(patch)
        logger.info("Patient profile updated using LLM extraction")
        return state
    except Exception as e:
        logger.error(f"Error updating patient profile: {str(e)}")
        state["error_message"] = f"Error updating patient profile: {str(e)}"
        state["has_error"] = True
        return state 