# Input processor node for LangGraph

from typing import Dict, Any
from langchain_core.messages import HumanMessage
from utils.logging_config import logger

def process_input(state: Dict[str, Any]) -> Dict[str, Any]:
    """Process user input and initialize state."""
    
    try:
        # Get user input from state
        user_input = state.get("user_input", "")
        
        if not user_input:
            state["error_message"] = "No user input provided"
            state["has_error"] = True
            return state
        
        # Add user message to conversation history
        messages = state.get("messages", [])
        messages.append(HumanMessage(content=user_input))
        state["messages"] = messages
        
        # Initialize workflow control
        state["should_continue"] = True
        state["iteration_count"] = 0
        state["max_iterations"] = 5
        state["has_error"] = False
        state["error_message"] = None
        state["response_generated"] = False
        state["final_response"] = None
        
        # Initialize tool results
        state["tool_results"] = []
        state["current_tool"] = None
        
        logger.info(f"Processed user input: {user_input[:50]}...")
        
        return state
        
    except Exception as e:
        logger.error(f"Error processing input: {str(e)}")
        state["error_message"] = f"Error processing input: {str(e)}"
        state["has_error"] = True
        return state 