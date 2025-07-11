# Response generator node for LangGraph

from typing import Dict, Any
from langchain_core.messages import AIMessage
from utils.logging_config import logger

def generate_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate final response using LLM based on tool results and context."""
    
    try:
        user_input = state.get("user_input", "")
        tool_results = state.get("tool_results", [])
        retrieved_context = state.get("retrieved_context", [])
        
        # Build context from tool results
        context_str = ""
        if tool_results:
            context_str = "\n\nTool Results:\n"
            for result in tool_results:
                tool_name = result.get("tool", "Unknown")
                tool_output = result.get("output", "")
                context_str += f"- {tool_name}: {tool_output}\n"
        
        # Build memory context
        memory_str = ""
        if retrieved_context:
            memory_str = "\n\nRelevant Memory:\n"
            for item in retrieved_context:
                memory_str += f"- {item.get('content', '')}\n"
        
        # Create response prompt
        response_prompt = f"""Based on the user's input and the available information, provide a helpful and conversational response.

User Input: {user_input}
{context_str}
{memory_str}

Provide a clear, direct answer that addresses the user's question or request. Be helpful and conversational."""

        # For now, create a simple response (can be replaced with LLM call)
        if tool_results:
            # Use the last tool result as the response
            last_result = tool_results[-1]
            response = last_result.get("output", "I've processed your request.")
        else:
            response = "I understand your request. How can I help you further?"
        
        state["final_response"] = response
        state["response_generated"] = True
        state["should_continue"] = False
        
        # Add AI response to messages
        messages = state.get("messages", [])
        messages.append(AIMessage(content=response))
        state["messages"] = messages
        
        logger.info(f"Generated response: {response[:50]}...")
        
        return state
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        state["error_message"] = f"Error generating response: {str(e)}"
        state["has_error"] = True
        return state 