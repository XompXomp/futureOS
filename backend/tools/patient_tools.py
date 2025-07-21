from langchain.agents import Tool
from modules.patient_operations import PatientOperations

def create_patient_tools():
    def read_patient_profile_tool(state: dict) -> dict:
        result = PatientOperations.read_patient_profile(state)
        # Ensure patientProfile is propagated in state
        state['patientProfile'] = result.get('patientProfile', state.get('patientProfile'))
        return state

    def update_patient_profile_tool(state: dict) -> dict:
        result = PatientOperations.update_patient_profile(state)
        state['patientProfile'] = result.get('patientProfile', state.get('patientProfile'))
        return state

    return [
        Tool(
            name="read_patient_profile",
            func=read_patient_profile_tool,
            description="Read the full patient profile. Input: state dict."
        ),
        Tool(
            name="update_patient_profile",
            func=update_patient_profile_tool,
            description="Update the patient profile using natural language input. Input: state dict with 'user_input'."
        )
    ] 