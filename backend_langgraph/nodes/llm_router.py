# LLM router node for LangGraph

from typing import Dict, Any, List
from langchain_core.messages import AIMessage
from utils.logging_config import logger

def route_to_tools(state: Dict[str, Any]) -> Dict[str, Any]:
    """Route user input to appropriate tools using LLM decision making."""
    
    try:
        user_input = state.get("user_input", "")
        retrieved_context = state.get("retrieved_context", [])
        
        # Build context from memory
        context_str = ""
        if retrieved_context:
            context_str = "\n\nRelevant context from memory:\n"
            for item in retrieved_context:
                context_str += f"- {item.get('content', '')}\n"
        
        # Create routing prompt
        routing_prompt = f"""Based on the user's input, determine which tools should be used.

                        User Input: {user_input}
                        {context_str}

                        Available tools:
                        - read_patient_profile: When user asks about their personal/medical information
                        - update_patient_profile: When user wants to update their information
                        - search_documents: When user asks about documents or files
                        - read_file: When user wants to read a specific file
                        - write_file: When user wants to create or modify a file
                        - search_web: When user asks for current information or research
                        - summarize_text: When user wants to summarize content
                        - query_database: When user asks about stored data

                        Respond with a JSON list of tool names to use, or "none" if no tools are needed.
                        Example: ["read_patient_profile"] or ["search_web", "summarize_text"] or "none"

                        Tool selection:
                        """
        
        # For now, use simple keyword matching (can be replaced with LLM call)
        tools_to_use = []
        
        user_input_lower = user_input.lower()
        
        # Patient profile operations
        if any(word in user_input_lower for word in ["my", "me", "myself", "patient", "profile"]):
            if any(word in user_input_lower for word in ["update", "change", "modify", "edit"]):
                tools_to_use.append("update_patient_profile")
            else:
                tools_to_use.append("read_patient_profile")
        
        # File operations
        elif any(word in user_input_lower for word in ["file", "document", "read", "write", "create"]):
            if any(word in user_input_lower for word in ["write", "create", "save"]):
                tools_to_use.append("write_file")
            else:
                tools_to_use.append("read_file")
        
        # Web search
        elif any(word in user_input_lower for word in ["search", "find", "current", "latest", "news"]):
            tools_to_use.append("search_web")
        
        # Text processing
        elif any(word in user_input_lower for word in ["summarize", "summary", "summarize"]):
            tools_to_use.append("summarize_text")
        
        # Database operations
        elif any(word in user_input_lower for word in ["database", "data", "query", "search"]):
            tools_to_use.append("query_database")
        
        state["tools_to_use"] = tools_to_use
        state["current_tool"] = tools_to_use[0] if tools_to_use else None
        
        logger.info(f"Routed to tools: {tools_to_use}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in routing: {str(e)}")
        state["tools_to_use"] = []
        state["current_tool"] = None
        return state 