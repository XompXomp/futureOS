from typing import Dict, Any
from langgraph.graph import StateGraph, END
from state.schema import PatientState
from nodes.input_processor import process_input
from agents.orchestrator_agent import OrchestratorAgent

# Instantiate the orchestrator agent
orchestrator_agent = OrchestratorAgent()

def create_multi_agent_graph() -> StateGraph:
    """Create the main LangGraph workflow for the multi-agent system."""
    workflow = StateGraph(PatientState)

    # Add nodes
    workflow.add_node("process_input", process_input)
    workflow.add_node("agent_executor", orchestrator_agent.handle)

    # Define the simplified workflow
    workflow.set_entry_point("process_input")
    workflow.add_edge("process_input", "agent_executor")
    workflow.add_edge("agent_executor", END)

    return workflow

def create_initial_state(user_input: str) -> Dict[str, Any]:
    """Create initial state for the multi-agent workflow."""
    from config.settings import settings
    try:
        initial_state = {
            "user_input": user_input,
            "messages": [],
            "patient_profile": {},
            "profile_updated": False,
            "tool_results": [],
            "current_tool": None,
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
        from utils.logging_config import logger
        logger.error(f"Error creating initial state: {str(e)}")
        raise 