import asyncio
from typing import Dict, Any
from tools.json_tools import read_json_file, write_json_file, list_json_files
from tools.memory_tools import create_memory_tools
from utils.logging_config import logger
from config.settings import settings
from langchain_community.chat_models import ChatOllama
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
import json
import os

class JsonAgent:
    def __init__(self, agent_id: str = "json_agent"):
        # Initialize memory system for this agent
        self.agent_id = agent_id
        self.memory_tools = create_memory_tools(agent_id)
        
        # JSON-specific tools
        self.json_tools = [read_json_file, write_json_file, list_json_files]
        
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
        self.tools = self.memory_tools + self.json_tools

    async def handle_async(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JSON-related tasks using LLM-driven reasoning with memory system."""
        try:
            # For now, use synchronous handler
            return self.handle(state)
        except Exception as e:
            logger.error(f"Error in JSON agent: {str(e)}")
            state["error_message"] = f"Error in JSON agent: {str(e)}"
            state["has_error"] = True
            return state

    def handle(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous handler for JSON-related tasks."""
        try:
            user_input = state.get("user_input", "")
            if not user_input:
                state["final_response"] = "I didn't receive any input to process."
                return state
            
            # Create a system prompt that describes the agent's capabilities
            system_prompt = f"""You are a JSON file management agent with access to memory tools and JSON file operations.\n\nAVAILABLE TOOLS:\n- read_json_file: Read JSON files from the data/docs directory\n- write_json_file: Write JSON data to files in the data/docs directory\n- list_json_files: List all JSON files in the data/docs directory\n- update_semantic_memory: Store new information in semantic memory\n- search_semantic_memory: Retrieve information from semantic memory\n- store_episodic_memory: Store successful interactions\n- search_episodic_memory: Retrieve past interactions\n- update_procedural_memory: Update behavior rules\n- get_procedural_memory: Retrieve behavior rules\n- optimize_prompt: Optimize prompts using procedural memory\n- get_memory_summary: Get comprehensive memory summary\n\nINSTRUCTIONS:\n1. When asked to read JSON files → Mention read_json_file tool\n2. When asked to write JSON files → Mention write_json_file tool\n3. When asked to list JSON files → Mention list_json_files tool\n4. The default directory for JSON operations is data/docs\n5. Be conversational and helpful with JSON-related queries\n\nEXAMPLES:\n- User: \"Read patient_profile.json\" → Mention read_json_file tool\n- User: \"List all JSON files\" → Mention list_json_files tool\n- User: \"Write data to config.json\" → Mention write_json_file tool\n\nUser input: {user_input}\n\nPlease provide a helpful response:"""

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
            if state.get("json_files"):
                files = state["json_files"]
                if isinstance(files, list):
                    state["final_response"] = "JSON files found: " + ", ".join(files)
                else:
                    state["final_response"] = str(files)
            elif state.get("final_response"):
                pass  # already set
            else:
                state["final_response"] = response_text or "No relevant JSON file result found."
            return state
        except Exception as e:
            logger.error(f"Error in JSON agent: {str(e)}")
            state["error_message"] = f"Error in JSON agent: {str(e)}"
            state["has_error"] = True
            return state 