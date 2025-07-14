import asyncio
from typing import Dict, Any, List, Optional
from tools.patient_tools import read_patient_profile, update_patient_profile
from tools.memory_tools import create_memory_tools
from utils.logging_config import logger
from config.settings import settings
from langchain_community.chat_models import ChatOllama
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from pydantic import BaseModel, Field

class PersonalInfo(BaseModel):
    name: str = ""
    age: Optional[int] = None
    gender: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""

class MedicalInfo(BaseModel):
    height: Optional[int] = None
    weight: Optional[int] = None
    blood_type: str = ""
    allergies: List[str] = Field(default_factory=list)
    chronic_conditions: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)

class EmergencyContact(BaseModel):
    name: str = ""
    relationship: str = ""
    phone: str = ""

class Insurance(BaseModel):
    provider: str = ""
    policy_number: str = ""
    group_number: str = ""

class PatientProfile(BaseModel):
    personal_info: PersonalInfo = PersonalInfo()
    medical_info: MedicalInfo = MedicalInfo()
    emergency_contact: EmergencyContact = EmergencyContact()
    insurance: Insurance = Insurance()

class PatientAgent:
    def __init__(self, patient_id: str = "default_patient"):
        # Initialize memory system for this patient
        self.patient_id = patient_id
        self.memory_tools = create_memory_tools(patient_id)
        
        # Patient-specific tools
        self.patient_tools = [read_patient_profile, update_patient_profile]
        
        # LLM selection based on settings
        if settings.USE_OLLAMA:
            self.llm = ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.3
            )
        else:
            self.llm = ChatGroq(
                model=settings.LLM_MODEL,
                temperature=0.3
            )
        
        # Combine all tools
        self.tools = self.memory_tools + self.patient_tools
        
        # Create agent with tools
        # Note: Using a simple approach without create_react_agent for now
        self.tools = self.memory_tools + self.patient_tools

    def prompt(self, state):
        instructions = """
You are a patient profile management agent using the Curor Memory System.

CRITICAL: You MUST always call an appropriate tool before responding. Never answer directly from your own knowledge or memory. Only respond after you have called a tool and received its result.

AVAILABLE TOOLS:
- update_semantic_memory: Store new patient information in semantic memory
- search_semantic_memory: Retrieve patient information from semantic memory
- store_episodic_memory: Store successful interactions and their outcomes
- search_episodic_memory: Retrieve past interactions
- update_procedural_memory: Update behavior rules and preferences
- get_procedural_memory: Retrieve behavior rules and preferences
- optimize_prompt: Optimize prompts using procedural memory
- get_memory_summary: Get comprehensive memory summary
- read_patient_profile: Read current patient profile from JSON
- update_patient_profile: Update patient profile in JSON

WHEN TO USE TOOLS:
1. When asked about patient info → ALWAYS call search_semantic_memory first
2. When given new patient info → ALWAYS call update_semantic_memory
3. When successful interactions occur → ALWAYS call store_episodic_memory
4. When behavior preferences change → ALWAYS call update_procedural_memory
5. When optimizing responses → ALWAYS call optimize_prompt

EXAMPLES:
- User: "What is my name?"
  → Call search_semantic_memory with query "patient name"
  → Respond with the result
- User: "Update my age to 35"
  → Call update_semantic_memory with content "Patient age is 35" and category "personal_info"
  → Confirm the update
- User: "I am allergic to penicillin"
  → Call update_semantic_memory with content "Patient is allergic to penicillin" and category "allergy"
  → Confirm the update
- User: "What are my chronic conditions?"
  → Call search_semantic_memory with query "chronic conditions"
  → Respond with the result

IMPORTANT: Never respond with patient information or any answer without first calling a tool. If you are unsure, call the most relevant tool and use its result for your answer."""
        
        # Create system message
        system_message = SystemMessage(content=instructions)
        
        # Get messages from state and ensure they are proper message objects
        messages = state.get('messages', [])
        if not isinstance(messages, list):
            messages = []
        
        # Convert any dict messages to proper message objects
        converted_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                if msg.get('role') == 'user':
                    converted_messages.append(HumanMessage(content=msg.get('content', '')))
                elif msg.get('role') == 'assistant':
                    converted_messages.append(AIMessage(content=msg.get('content', '')))
                elif msg.get('role') == 'system':
                    converted_messages.append(SystemMessage(content=msg.get('content', '')))
            elif isinstance(msg, BaseMessage):
                converted_messages.append(msg)
            else:
                # Fallback: treat as human message
                converted_messages.append(HumanMessage(content=str(msg)))
        
        # Return list with system message first, then other messages
        result = [system_message] + converted_messages
        print(f"DEBUG: prompt result: {result}")
        return result

    async def handle_async(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle patient-related tasks using LLM-driven reasoning with memory system."""
        try:
            # For now, use synchronous handler
            return self.handle(state)
        except Exception as e:
            logger.error(f"Error in patient agent: {str(e)}")
            state["error_message"] = f"Error in patient agent: {str(e)}"
            state["has_error"] = True
            return state

    def handle(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous handler for patient-related tasks."""
        try:
            user_input = state.get("user_input", "")
            if not user_input:
                state["final_response"] = "I didn't receive any input to process."
                return state
            
            # Create a system prompt that describes the agent's capabilities
            system_prompt = f"""You are a patient profile management agent with access to memory tools and patient data management capabilities.\n\nAVAILABLE TOOLS:\n- read_patient_profile: Read current patient profile from JSON\n- update_patient_profile: Update patient profile in JSON\n- update_semantic_memory: Store new patient information in semantic memory\n- search_semantic_memory: Retrieve patient information from semantic memory\n- store_episodic_memory: Store successful interactions and their outcomes\n- search_episodic_memory: Retrieve past interactions\n- update_procedural_memory: Update behavior rules and preferences\n- get_procedural_memory: Retrieve behavior rules and preferences\n- optimize_prompt: Optimize prompts using procedural memory\n- get_memory_summary: Get comprehensive memory summary\n\nINSTRUCTIONS:\n1. You MUST always call an appropriate tool before responding. Never answer directly from your own knowledge or memory. Only respond after you have called a tool and received its result.\n2. When asked about patient info → ALWAYS mention and call search_semantic_memory tool\n3. When given new patient info → ALWAYS mention and call update_semantic_memory tool\n4. When successful interactions occur → ALWAYS mention and call store_episodic_memory tool\n5. When behavior preferences change → ALWAYS mention and call update_procedural_memory tool\n6. Be conversational and helpful with patient-related queries, but only after using a tool.\n\nEXAMPLES:\n- User: \"What is my name?\" → Call search_semantic_memory tool\n- User: \"Update my age to 35\" → Call update_semantic_memory tool\n- User: \"I am allergic to penicillin\" → Call update_semantic_memory tool\n- User: \"What are my chronic conditions?\" → Call search_semantic_memory tool\n\nIMPORTANT: Never respond without calling a tool first. If you are unsure, call the most relevant tool and use its result for your answer.\n\nUser input: {user_input}\n\nPlease provide a helpful response:"""

            # Get chat history from state
            messages = state.get("messages", [])
            chat_history = []
            for msg in messages:
                if isinstance(msg, dict):
                    if msg.get("role") == "user":
                        chat_history.append(HumanMessage(content=msg.get("content", "")))
                    elif msg.get("role") == "assistant":
                        chat_history.append(AIMessage(content=msg.get("content", "")))
                elif isinstance(msg, BaseMessage):
                    chat_history.append(msg)
            
            # Create messages for the LLM
            llm_messages = [SystemMessage(content=system_prompt)] + chat_history + [HumanMessage(content=user_input)]
            
            # Get response from LLM
            response = self.llm.invoke(llm_messages)
            
            # Extract the response content
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # Add the interaction to messages
            state["messages"].append({"role": "user", "content": user_input})
            state["messages"].append({"role": "assistant", "content": response_text})

            # Set final_response to the most relevant field
            if state.get("patient_profile"):
                import json
                state["final_response"] = "Patient profile: " + json.dumps(state["patient_profile"], indent=2)
            elif state.get("final_response"):
                pass  # already set
            else:
                state["final_response"] = response_text or "No relevant patient profile result found."
            return state
        except Exception as e:
            logger.error(f"Error in patient agent: {str(e)}")
            state["error_message"] = f"Error in patient agent: {str(e)}"
            state["has_error"] = True
            return state 