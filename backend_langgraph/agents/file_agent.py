import asyncio
from typing import Dict, Any
from tools.file_tools import read_file, write_file
from tools.memory_tools import create_memory_tools
from utils.logging_config import logger
from config.settings import settings
from langchain_community.chat_models import ChatOllama
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

class FileAgent:
    def __init__(self, agent_id: str = "file_agent"):
        # Initialize memory system for this agent
        self.agent_id = agent_id
        self.memory_tools = create_memory_tools(agent_id)
        
        # File-specific tools
        self.file_tools = [read_file, write_file]
        
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
        self.tools = self.memory_tools + self.file_tools

    async def handle_async(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file-related tasks using LLM-driven reasoning with memory system."""
        try:
            # For now, use synchronous handler
            return self.handle(state)
        except Exception as e:
            logger.error(f"Error in file agent: {str(e)}")
            state["error_message"] = f"Error in file agent: {str(e)}"
            state["has_error"] = True
            return state

    def handle(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous handler for file-related tasks."""
        try:
            user_input = state.get("user_input", "")
            if not user_input:
                state["final_response"] = "I didn't receive any input to process."
                return state
            
            # Create a system prompt that describes the agent's capabilities
            system_prompt = f"""You are a file management agent with access to memory tools and file operations.\n\nAVAILABLE TOOLS:\n- read_file: Read files from the data/docs directory\n- write_file: Write content to files in the data/docs directory\n- update_semantic_memory: Store new information in semantic memory\n- search_semantic_memory: Retrieve information from semantic memory\n- store_episodic_memory: Store successful interactions\n- search_episodic_memory: Retrieve past interactions\n- update_procedural_memory: Update behavior rules\n- get_procedural_memory: Retrieve behavior rules\n- optimize_prompt: Optimize prompts using procedural memory\n- get_memory_summary: Get comprehensive memory summary\n\nINSTRUCTIONS:\n1. When asked to read files → Mention read_file tool\n2. When asked to write files → Mention write_file tool\n3. The default directory for file operations is data/docs\n4. Be conversational and helpful with file-related queries\n\nEXAMPLES:\n- User: \"Read example.txt\" → Mention read_file tool\n- User: \"Write 'Hello World' to test.txt\" → Mention write_file tool\n\nUser input: {user_input}\n\nPlease provide a helpful response:"""

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
            if state.get("file_content"):
                state["final_response"] = state["file_content"]
            elif state.get("final_response"):
                pass  # already set
            else:
                state["final_response"] = response_text or "No relevant file content found."
            return state
        except Exception as e:
            logger.error(f"Error in file agent: {str(e)}")
            state["error_message"] = f"Error in file agent: {str(e)}"
            state["has_error"] = True
            return state 