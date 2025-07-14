import asyncio
from typing import Dict, Any
from tools.web_search_tools import search_web
from tools.memory_tools import create_memory_tools
from utils.logging_config import logger
from config.settings import settings
from langchain_community.chat_models import ChatOllama
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

class WebAgent:
    def __init__(self, agent_id: str = "web_agent"):
        # Initialize memory system for this agent
        self.agent_id = agent_id
        self.memory_tools = create_memory_tools(agent_id)
        
        # Web-specific tools
        self.web_tools = [search_web]
        
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
        self.tools = self.memory_tools + self.web_tools

    async def handle_async(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle web-related tasks using LLM-driven reasoning with memory system."""
        try:
            # For now, use synchronous handler
            return self.handle(state)
        except Exception as e:
            logger.error(f"Error in web agent: {str(e)}")
            state["error_message"] = f"Error in web agent: {str(e)}"
            state["has_error"] = True
            return state

    def handle(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous handler for web-related tasks using ReAct pattern."""
        try:
            user_input = state.get("user_input", "")
            if not user_input:
                state["final_response"] = "I didn't receive any input to process."
                return state
            
            # Create ReAct prompt template
            react_prompt = f"""You are a web search agent with access to memory tools and web search capabilities. You can think, act, and observe.

AVAILABLE TOOLS:
- search_web: Search the web for information using Google PSE
- update_semantic_memory: Store new information in semantic memory
- search_semantic_memory: Retrieve information from semantic memory
- store_episodic_memory: Store successful interactions
- search_episodic_memory: Retrieve past interactions
- update_procedural_memory: Update behavior rules
- get_procedural_memory: Retrieve behavior rules
- optimize_prompt: Optimize prompts using procedural memory
- get_memory_summary: Get comprehensive memory summary

INSTRUCTIONS:
1. You MUST always call an appropriate tool before responding. Never answer directly from your own knowledge or memory. Only respond after you have called a tool and received its result.
2. If you need to search the web, write: "Action: search_web"
3. After the tool runs, you'll see the result
4. Integrate the search result into your response if helpful

IMPORTANT: Never respond without calling a tool first. If you are unsure, call the most relevant tool and use its result for your answer.

User input: {user_input}

Let's start:"""

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
            llm_messages = [SystemMessage(content=react_prompt)] + chat_history + [HumanMessage(content=user_input)]
            
            # Get initial response from LLM
            response = self.llm.invoke(llm_messages)
            
            # Extract the response content
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # Check if LLM wants to call a tool
            tool_called = False
            tool_result = None
            if isinstance(response_text, str) and "Action:" in response_text:
                # Parse tool call from LLM response
                lines = response_text.split('\n')
                for line in lines:
                    if line.strip().startswith("Action:"):
                        tool_name = line.strip().replace("Action:", "").strip()
                        logger.info(f"LLM requested tool: {tool_name}")
                        
                        # Find and call the tool
                        tool_result = self._call_tool(tool_name, state)
                        logger.info(f"Tool called: {tool_name}")
                        logger.info(f"Tool result type: {type(tool_result)}")
                        logger.info(f"Tool result: {tool_result}")
                        if tool_result:
                            tool_called = True
                            logger.info(f"Tool result: {tool_result[:200]}...")
                            # Add tool result to response
                            response_text += f"\n\nTool Result: {tool_result}"
                            break
            # Fallback: If no tool was called, always call search_web with user input
            if not tool_called:
                logger.info("No tool call detected in LLM response. Forcing search_web tool call.")
                tool_result = self._call_tool("search_web", state)
                tool_called = True
                response_text += f"\n\nTool Result: {tool_result}"
            
            # Add the interaction to messages
            state["messages"].append({"role": "user", "content": user_input})
            state["messages"].append({"role": "assistant", "content": response_text})

            # Set final_response to the most relevant field
            if tool_called and tool_result and isinstance(response_text, str) and not response_text.strip().startswith("Action:"):
                # If a tool was called and we have a meaningful LLM response (not just "Action: tool_name")
                # Use the LLM's response as primary, with tool result as supplement
                state["final_response"] = response_text.replace("Action: " + tool_name, "").strip()
                if tool_result and tool_result != "Tool executed successfully":
                    state["final_response"] += f"\n\nTool Result: {tool_result}"
            elif tool_called and tool_result:
                # If only tool result is meaningful, use it
                state["final_response"] = tool_result
            elif state.get("search_message"):
                state["final_response"] = state["search_message"]
            elif state.get("search_results"):
                # Format search_results if present
                results = state["search_results"]
                formatted = "Web search results:\n\n"
                for i, result in enumerate(results, 1):
                    if isinstance(result, dict):
                        formatted += f"{i}. {result.get('metadata', {}).get('title', 'No title')}\n"
                        formatted += f"   URL: {result.get('metadata', {}).get('url', 'No URL')}\n"
                        formatted += f"   Content: {result.get('content', '')[:200]}...\n"
                        formatted += f"   Similarity Score: {result.get('similarity_score', 0):.3f}\n\n"
                state["final_response"] = formatted
            elif state.get("final_response"):
                pass  # already set
            else:
                state["final_response"] = response_text or "No relevant web search result found."
            return state
        except Exception as e:
            logger.error(f"Error in web agent: {str(e)}")
            state["error_message"] = f"Error in web agent: {str(e)}"
            state["has_error"] = True
            return state

    def _call_tool(self, tool_name: str, state: Dict[str, Any]) -> str:
        """Call a specific tool by name."""
        try:
            from tools.web_search_tools import search_web
            
            # Map tool names to functions
            tool_map = {
                "search_web": search_web,
                "update_semantic_memory": self.memory_tools[0] if self.memory_tools else None,
                "search_semantic_memory": self.memory_tools[1] if len(self.memory_tools) > 1 else None,
                "store_episodic_memory": self.memory_tools[2] if len(self.memory_tools) > 2 else None,
                "search_episodic_memory": self.memory_tools[3] if len(self.memory_tools) > 3 else None,
                "update_procedural_memory": self.memory_tools[4] if len(self.memory_tools) > 4 else None,
                "get_procedural_memory": self.memory_tools[5] if len(self.memory_tools) > 5 else None,
                "optimize_prompt": self.memory_tools[6] if len(self.memory_tools) > 6 else None,
                "get_memory_summary": self.memory_tools[7] if len(self.memory_tools) > 7 else None,
            }
            
            tool_func = tool_map.get(tool_name)
            if tool_func:
                # Call the tool
                result_state = tool_func(state)
                
                # Extract result based on tool type
                if tool_name == "search_web":
                    return result_state.get("search_message", "No search results")
                elif tool_name.startswith("search_semantic_memory"):
                    return result_state.get("search_results", "No semantic memory results")
                else:
                    return "Tool executed successfully"
            else:
                return f"Tool '{tool_name}' not found"
                
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {str(e)}")
            return f"Error calling tool: {str(e)}" 