# Main LangGraph workflow for patient management

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langmem.knowledge.extraction import Memory
from utils.logging_config import logger
from config.settings import settings
from state.schema import PatientState

# Import nodes
from nodes.input_processor import process_input
from nodes.memory_retriever import retrieve_memory
from nodes.llm_router import route_to_tools
from nodes.response_generator import generate_response

# Import tools
from tools.patient_tools import read_patient_profile, update_patient_profile
from tools.file_tools import read_file, write_file
from tools.web_search_tools import search_web
from tools.text_tools import summarize_text, query_database

def create_patient_graph() -> StateGraph:
    """Create the main LangGraph workflow for patient management."""
    
    # Create the graph
    workflow = StateGraph(PatientState)
    
    # Add nodes
    workflow.add_node("process_input", process_input)
    workflow.add_node("retrieve_memory", retrieve_memory)
    workflow.add_node("route_to_tools", route_to_tools)
    workflow.add_node("read_patient_profile", read_patient_profile)
    workflow.add_node("update_patient_profile", update_patient_profile)
    workflow.add_node("read_file", read_file)
    workflow.add_node("write_file", write_file)
    workflow.add_node("search_web", search_web)
    workflow.add_node("summarize_text", summarize_text)
    workflow.add_node("query_database", query_database)
    workflow.add_node("generate_response", generate_response)
    
    # Define the main workflow
    workflow.set_entry_point("process_input")
    
    # Add edges
    workflow.add_edge("process_input", "retrieve_memory")
    workflow.add_edge("retrieve_memory", "route_to_tools")
    
    # Add conditional edges for tool execution
    workflow.add_conditional_edges(
        "route_to_tools",
        lambda state: state["current_tool"] if state.get("current_tool") in [
            "read_patient_profile",
            "update_patient_profile",
            "read_file",
            "write_file",
            "search_web",
            "summarize_text",
            "query_database",
            "generate_response"
        ] else "generate_response",
        {
            "read_patient_profile": "read_patient_profile",
            "update_patient_profile": "update_patient_profile",
            "read_file": "read_file",
            "write_file": "write_file",
            "search_web": "search_web",
            "summarize_text": "summarize_text",
            "query_database": "query_database",
            "generate_response": "generate_response"
        }
    )
    
    # All tools lead to response generation
    workflow.add_edge("read_patient_profile", "generate_response")
    workflow.add_edge("update_patient_profile", "generate_response")
    workflow.add_edge("read_file", "generate_response")
    workflow.add_edge("write_file", "generate_response")
    workflow.add_edge("search_web", "generate_response")
    workflow.add_edge("summarize_text", "generate_response")
    workflow.add_edge("query_database", "generate_response")
    
    # Response generation is the end
    workflow.add_edge("generate_response", END)
    
    return workflow

def initialize_memory() -> Memory:
    """Initialize LangMem memory."""
    try:
        memory = Memory(content="Initial memory for patient workflow.")
        logger.info("LangMem memory initialized successfully")
        return memory
    except Exception as e:
        logger.error(f"Error initializing memory: {str(e)}")
        raise

def create_initial_state(user_input: str) -> Dict[str, Any]:
    """Create initial state for the LangGraph workflow."""
    
    try:
        # Initialize memory
        memory = initialize_memory()
        
        # Create initial state
        initial_state = {
            "user_input": user_input,
            "messages": [],
            "patient_profile": {},
            "profile_updated": False,
            "tool_results": [],
            "current_tool": None,
            "memory": memory,
            "retrieved_context": [],
            "should_continue": True,
            "iteration_count": 0,
            "max_iterations": settings.MAX_ITERATIONS,
            "error_message": None,
            "has_error": False,
            "final_response": None,
            "response_generated": False
        }
        
        return initial_state
        
    except Exception as e:
        logger.error(f"Error creating initial state: {str(e)}")
        raise 