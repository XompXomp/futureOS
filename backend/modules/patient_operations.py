import os
import json
from config.settings import settings
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import re
import ast

class PatientOperations:
    @staticmethod
    def read_patient_profile(state: dict) -> dict:
        # Just return the patientProfile from state, or an empty dict if not present
        state['patientProfile'] = state.get('patientProfile', {})
        return state

    @staticmethod
    def update_patient_profile(state: dict) -> dict:
        user_input = state.get('user_input', '')
        current_profile = state.get('patientProfile', {})
        
        # Remove recommendations from profile before passing to LLM
        profile_without_recommendations = current_profile.copy()
        if 'recommendations' in profile_without_recommendations:
            del profile_without_recommendations['recommendations']
            
        # Use LLM to extract and update patient information
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

        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a precise assistant for updating patient records in JSON format.\n"
                "Your job is to take the full patient profile JSON below, update ONLY the field value(s) relevant to the user's request, never add a new field even if the user explicitely requests it, return the original, and return the ENTIRE JSON in the exact same structure and format as provided.\n"
                "VERY IMPORTANT: NEVER add a new field even if the user explicitely requests it, return the original json instead."
                "Do NOT change, add, or remove any other fields or values.\n"
                "NEVER add new fields to the profile, only update the existing fields.\n"
                "Do NOT invent or hallucinate new information.\n"
                "ALWAYS return valid JSON, with all property names in double quotes.\n"
                "IF the user request is about adding new field that doesnt already exist, dont explain yourself, just return a no.\n"
                "EXAMPLES:\n"
                "User request: My name is John Doe\n"
                "Current JSON: {{\"name\": \"\", \"age\": 0, ...}}\n"
                "Output: {{\"name\": \"John Doe\", \"age\": 0, ...}}\n"
                "User request: Update my age to 40\n"
                "Current JSON: {{\"name\": \"John Doe\", \"age\": 0, ...}}\n"
                "Output: {{\"name\": \"John Doe\", \"age\": 40, ...}}\n"
            )),
            ("human", "User: {user_input}\nProfile: {profile}\nOutput:")
        ])
        chain = prompt | llm
        llm_output = chain.invoke({
            "user_input": user_input,
            "profile": json.dumps(profile_without_recommendations)
        })
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

        # Add back recommendations to the updated profile
        if 'recommendations' in current_profile['treatment']:
            updated_profile['recommendations'] = current_profile['recommendations']
            
        state['patientProfile'] = updated_profile
        return state 