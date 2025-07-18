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

import re
import ast


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
            ("system", (
                "You are a precise assistant for updating patient records in JSON format. Your job is to take the full patient profile JSON below, update ONLY the field(s) relevant to the user's request, and return the ENTIRE JSON in the exact same structure and format as provided. Do not change, add, or remove any other fields or values. Do not invent or hallucinate new information. If the request is ambiguous, make no changes and return the original JSON.\n\n"
                "Current patient profile JSON:"
                "{profile}\n\n"
                "User request: {user_input}\n\n"
                "Return ONLY the full, updated JSON. Do not include any explanation, comments, or extra text. Do not change the structure or formatting of the JSON except for the requested update. ENSURE that the JSON format text returned has all property names enclosed in double quotes."
            )),
            ("human", "User: {user_input}\nProfile: {profile}\nOutput:")
        ])
        chain = prompt | llm
        # Run the LLM to get the updated profile
        llm_output = chain.invoke({
            "user_input": user_input,
            "profile": json.dumps(current_profile)
        })

        if (settings.DEBUG):
            print("--------------------------------")
            print(f"LLM Output: {llm_output}")
            print("--------------------------------")

        llm_json_str = str(llm_output.content)

        match = re.search(r'\{.*\}', llm_json_str, re.DOTALL)
        if match:
            try:
                updated_profile = json.loads(match.group(0))
            except Exception:
                try:
                    updated_profile = ast.literal_eval(match.group(0))
                except Exception:
                    updated_profile = current_profile  # fallback
        else:
            updated_profile = current_profile  # fallback

        if (settings.DEBUG):
            print("--------------------------------")
            print(f"Updated profile: {updated_profile}")
            print("--------------------------------")
            
        # Save updated profile directly
        profile_path = settings.PATIENT_PROFILE_PATH
        with open(profile_path, 'w') as f:
            json.dump(updated_profile, f, indent=2)
        # Debug: Read back the file to confirm update
        try:
            with open(profile_path, 'r') as f:
                file_contents = f.read()
            logger.info(f"[DEBUG] Profile after update (from disk): {file_contents}")
        except Exception as e:
            logger.error(f"[DEBUG] Could not read profile after update: {e}")
        tool_results = state.get("tool_results", [])
        tool_results.append({
            "tool": "update_patient_profile",
            "output": f"Patient profile updated using LLM extraction."
        })
        state["tool_results"] = tool_results
        state["patient_profile"] = updated_profile
        state["profile_updated"] = True
        logger.info("Patient profile updated using LLM extraction")
        return state
    except Exception as e:
        logger.error(f"Error updating patient profile: {str(e)}")
        state["error_message"] = f"Error updating patient profile: {str(e)}"
        state["has_error"] = True
        return state 