import os
import json
from config.settings import settings
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import re
import ast
import copy

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
        profile_without_recommendations = copy.deepcopy(current_profile)
        for t in profile_without_recommendations['treatment']:
            t.pop('recommendations', None)  # safer than del
            
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
                "Your job is to update the patient profile based on the user's request.\n\n"
                "RULES:\n"
                "1. ONLY update existing fields in the profile - never add new top-level fields\n"
                "2. You CAN add items to existing lists (like medicationList, allergies, dailyChecklist)\n"
                "3. You CAN update values within existing nested objects\n"
                "4. If the user requests to add a completely new field that doesn't exist, return the original JSON unchanged\n"
                "5. Always return the ENTIRE JSON in the exact same structure\n"
                "6. Do NOT invent or hallucinate new information\n"
                "7. ALWAYS return valid JSON with all property names in double quotes\n\n"
                "EXAMPLES:\n"
                "User: 'Add panadol to my medications'\n"
                "Action: Add 'panadol' to the existing 'medicationList' array\n\n"
                "User: 'Add a new field called symptoms'\n"
                "Action: Return original JSON unchanged (new field not allowed)\n\n"
                "User: 'Update my age to 40'\n"
                "Action: Update the 'age' field to 40\n\n"
                "User: 'Add walking to my daily checklist'\n"
                "Action: Add 'walking' to the existing 'dailyChecklist' array\n\n"
                "IMPORTANT: If you cannot make the requested change (e.g., adding a new field), return the original JSON without explanation.\n"
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

        i = 0
        for t in current_profile['treatment']:
            if 'recommendations' in t:
                updated_profile['treatment'][i]['recommendations'] = current_profile['treatment'][i]['recommendations']
                i += 1

        # if 'recommendations' in current_profile:
        #     updated_profile['recommendations'] = current_profile['recommendations']
            
        state['patientProfile'] = updated_profile
        return state 