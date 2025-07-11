# State schema for LangGraph patient management system

from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langmem.knowledge.extraction import Memory

class PatientState(TypedDict):
    """State schema for the patient management LangGraph."""
    
    # User input and conversation
    messages: List[BaseMessage]
    user_input: str
    
    # Patient profile data
    patient_profile: Dict[str, Any]
    profile_updated: bool
    
    # Tool execution results
    tool_results: List[Dict[str, Any]]
    current_tool: Optional[str]
    
    # Memory and context
    memory: Memory
    retrieved_context: List[Dict[str, Any]]
    
    # Workflow control
    should_continue: bool
    iteration_count: int
    max_iterations: int
    
    # Error handling
    error_message: Optional[str]
    has_error: bool
    
    # Final response
    final_response: Optional[str]
    response_generated: bool 