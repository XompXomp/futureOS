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
            description=(
                "Use this tool when the user is asking to view or retrieve information "
                "from their patient profile, such as sleep schedule, medications, or allergies.\n\n"
                "**Examples:**\n"
                "- 'What medications am I taking?'\n"
                "- 'Do I have any allergies?'\n"
                "- 'What’s in my patient profile?'\n"
                "- 'Can you show me my daily routine?'\n"
                "- 'What did I tell you about my sleep?'\n\n"
                "**Input:** Full `state` dict. No need for specific fields."
            )
        ),
        Tool(
            name="update_patient_profile",
            func=update_patient_profile_tool,
            description=(
                "Use this tool when the user wants to change, update, or add new information to their profile, "
                "based on natural language instructions.\n\n"
                "**Examples:**\n"
                "- 'I sleep for 10 hours every night'\n"
                "- 'Add yoga to my morning routine'\n"
                "- 'Update my medication to include insulin'\n"
                "- 'Change my sleep quality to poor'\n"
                "- 'I have a peanut allergy'\n"
                "- 'Remove aspirin from my medications'\n\n"
                "**Input:** `state` dict with the field `'user_input'` containing the user's instruction."
            )
        )
    ] 