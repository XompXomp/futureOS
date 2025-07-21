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
                "You are a precise assistant for updating patient records in JSON format. Your job is to take the full patient profile JSON below, update ONLY the field(s) relevant to the user's request, and return the ENTIRE JSON in the exact same structure and format as provided. Do not change, add, or remove any other fields or values. Do not invent or hallucinate new information. If the request is ambiguous, make no changes and return the original JSON.\n\n"
                "Current patient profile JSON:"
                "{profile}\n\n"
                "User request: {user_input}\n\n"
                "Return ONLY the full, updated JSON. Do not include any explanation, comments, or extra text. Do not change the structure or formatting of the JSON except for the requested update. ENSURE that the JSON format text returned has all property names enclosed in double quotes."
            )),
            ("human", "User: {user_input}\nProfile: {profile}\nOutput:")
        ])
        chain = prompt | llm
        llm_output = chain.invoke({
            "user_input": user_input,
            "profile": json.dumps(current_profile)
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
        state['patientProfile'] = updated_profile
        return state 