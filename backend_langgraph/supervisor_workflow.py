#!/usr/bin/env python3
"""LangGraph Supervisor-based multi-agent workflow."""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from typing import Dict, Any
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langchain_community.chat_models import ChatOllama
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

from config.settings import settings
from tools.patient_tools import read_patient_profile, update_patient_profile
from tools.web_search_tools import search_web
from tools.text_tools import summarize_text, query_database, extract_keywords
from tools.file_tools import read_file, write_file
from tools.json_tools import read_json_file, write_json_file, list_json_files
from tools.memory_tools import create_memory_tools
from utils.logging_config import logger

class SupervisorWorkflow:
    def __init__(self):
        """Initialize the supervisor workflow with all agents."""
        # Initialize LLM
        if settings.USE_OLLAMA:
            self.model = ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.3
            )
        else:
            self.model = ChatGroq(
                model=settings.LLM_MODEL,
                temperature=0.3
            )
        
        # Create memory tools for each agent
        self.patient_memory_tools = create_memory_tools("patient_agent")
        self.web_memory_tools = create_memory_tools("web_agent")
        self.text_memory_tools = create_memory_tools("text_agent")
        self.file_memory_tools = create_memory_tools("file_agent")
        self.json_memory_tools = create_memory_tools("json_agent")
        
        # Create specialized agents using create_react_agent
        self.patient_agent = create_react_agent(
            model=self.model,
            tools=[read_patient_profile, update_patient_profile] + self.patient_memory_tools,
            name="patient_agent",
            prompt="""You are a patient profile management agent with access to memory tools and patient data operations.

AVAILABLE TOOLS:
- read_patient_profile: Read current patient profile from JSON
- update_patient_profile: Update patient profile in JSON
- update_semantic_memory: Store new information in semantic memory
- search_semantic_memory: Retrieve information from semantic memory
- store_episodic_memory: Store successful interactions
- search_episodic_memory: Retrieve past interactions
- update_procedural_memory: Update behavior rules
- get_procedural_memory: Retrieve behavior rules
- optimize_prompt: Optimize prompts using procedural memory
- get_memory_summary: Get comprehensive memory summary

INSTRUCTIONS:
1. Always provide a conversational response to the user's input
2. When asked about patient info → Use read_patient_profile and provide the information conversationally
3. When given new patient info → Use update_patient_profile and confirm the update
4. Be conversational, helpful, and provide meaningful responses

EXAMPLES:
- User: "What is my name?" → Check patient profile and respond: "Your name is [name]"
- User: "Update my age to 35" → Update profile and respond: "I've updated your age to 35"
- User: "I am allergic to penicillin" → Update profile and respond: "I've recorded your penicillin allergy"
- User: "What are my chronic conditions?" → Check profile and list conditions conversationally"""
        )
        
        self.web_agent = create_react_agent(
            model=self.model,
            tools=[search_web] + self.web_memory_tools,
            name="web_agent",
            prompt="""You are a web search agent with access to memory tools and web search capabilities.

AVAILABLE TOOLS:
- search_web: Search the web for current information
- update_semantic_memory: Store new information in semantic memory
- search_semantic_memory: Retrieve information from semantic memory
- store_episodic_memory: Store successful interactions
- search_episodic_memory: Retrieve past interactions
- update_procedural_memory: Update behavior rules
- get_procedural_memory: Retrieve behavior rules
- optimize_prompt: Optimize prompts using procedural memory
- get_memory_summary: Get comprehensive memory summary

INSTRUCTIONS:
1. ALWAYS provide a conversational response to the user's input
2. When asked for current information, news, or facts → Use search_web tool and provide the results conversationally
3. NEVER output tool call syntax like <|python_tag|>search_web(...) - instead EXECUTE the tool and return the conversational result
4. Be conversational, helpful, and provide meaningful responses
5. If the search doesn't find relevant information, say so conversationally

EXAMPLES:
- User: "Who is the current US president?" → Search web and respond: "According to my search, [current president] is the current US president..."
- User: "What's the weather like?" → Search web and provide: "Based on current information, the weather is..."
- User: "When did superman release?" → Search web and respond: "Superman first appeared in Action Comics #1 on April 18, 1938..."

IMPORTANT: Always execute tools and provide conversational responses, never output raw tool calls."""
        )
        
        self.text_agent = create_react_agent(
            model=self.model,
            tools=[summarize_text, query_database, extract_keywords] + self.text_memory_tools,
            name="text_agent",
            prompt="""You are a text processing agent with access to various tools for text analysis and memory management.

AVAILABLE TOOLS:
- summarize_text: Summarize long text content
- query_database: Query the database for information  
- extract_keywords: Extract key terms from text
- update_semantic_memory: Store new information in semantic memory
- search_semantic_memory: Retrieve information from semantic memory
- store_episodic_memory: Store successful interactions
- search_episodic_memory: Retrieve past interactions
- update_procedural_memory: Update behavior rules
- get_procedural_memory: Retrieve behavior rules
- optimize_prompt: Optimize prompts using procedural memory
- get_memory_summary: Get comprehensive memory summary

INSTRUCTIONS:
1. Always provide a conversational response to the user's input
2. If the user asks about available agents, list all 5 agents: patient_agent, web_agent, text_agent, file_agent, json_agent
3. For greetings like 'Hello', 'Hi', respond warmly and ask how you can help
4. If the user asks for text analysis, use summarize_text or extract_keywords
5. If the user asks for database queries, use query_database
6. Be conversational, helpful, and provide meaningful responses

EXAMPLES:
- User: 'Hello' → 'Hello! How can I help you today?'
- User: 'What agents do you have?' → 'I have 5 agents: patient_agent, web_agent, text_agent, file_agent, json_agent'
- User: 'How are you?' → 'I'm doing well, thank you for asking! How can I assist you?'"""
        )
        
        self.file_agent = create_react_agent(
            model=self.model,
            tools=[read_file, write_file] + self.file_memory_tools,
            name="file_agent",
            prompt="""You are a file management agent with access to memory tools and file operations.

AVAILABLE TOOLS:
- read_file: Read files from the data/docs directory
- write_file: Write content to files in the data/docs directory
- update_semantic_memory: Store new information in semantic memory
- search_semantic_memory: Retrieve information from semantic memory
- store_episodic_memory: Store successful interactions
- search_episodic_memory: Retrieve past interactions
- update_procedural_memory: Update behavior rules
- get_procedural_memory: Retrieve behavior rules
- optimize_prompt: Optimize prompts using procedural memory
- get_memory_summary: Get comprehensive memory summary

INSTRUCTIONS:
1. When asked to read files → Use read_file tool
2. When asked to write files → Use write_file tool
3. The default directory for file operations is data/docs
4. Be conversational and helpful with file-related queries

EXAMPLES:
- User: "Read example.txt" → Use read_file tool
- User: "Write 'Hello World' to test.txt" → Use write_file tool"""
        )
        
        self.json_agent = create_react_agent(
            model=self.model,
            tools=[read_json_file, write_json_file, list_json_files] + self.json_memory_tools,
            name="json_agent",
            prompt="""You are a JSON file management agent with access to memory tools and JSON file operations.

AVAILABLE TOOLS:
- read_json_file: Read JSON files from the data/docs directory
- write_json_file: Write JSON data to files in the data/docs directory
- list_json_files: List all JSON files in the data/docs directory
- update_semantic_memory: Store new information in semantic memory
- search_semantic_memory: Retrieve information from semantic memory
- store_episodic_memory: Store successful interactions
- search_episodic_memory: Retrieve past interactions
- update_procedural_memory: Update behavior rules
- get_procedural_memory: Retrieve behavior rules
- optimize_prompt: Optimize prompts using procedural memory
- get_memory_summary: Get comprehensive memory summary

INSTRUCTIONS:
1. When asked to read JSON files → Use read_json_file tool
2. When asked to write JSON files → Use write_json_file tool
3. When asked to list JSON files → Use list_json_files tool
4. The default directory for JSON operations is data/docs
5. Be conversational and helpful with JSON-related queries

EXAMPLES:
- User: "Read patient_profile.json" → Use read_json_file tool
- User: "List all JSON files" → Use list_json_files tool
- User: "Write data to config.json" → Use write_json_file tool"""
        )
        
        # Debug: Print agent types
        logger.info(f"Patient agent type: {type(self.patient_agent)}")
        logger.info(f"Text agent type: {type(self.text_agent)}")
        logger.info(f"Web agent type: {type(self.web_agent)}")
        logger.info(f"File agent type: {type(self.file_agent)}")
        logger.info(f"JSON agent type: {type(self.json_agent)}")
        
        # Create supervisor workflow
        self.workflow = create_supervisor(
            [self.patient_agent, self.web_agent, self.text_agent, self.file_agent, self.json_agent],
            model=self.model,
            prompt="""
You are a supervisor for a team of specialized agents in a healthcare AI system.

AVAILABLE AGENTS:
- patient_agent: Handles patient profile queries, updates, and medical information
- web_agent: Handles web searches and online information gathering
- text_agent: Handles text processing, summarization, general conversation, and listing all available agents
- file_agent: Handles file operations like reading, writing, and managing documents
- json_agent: Handles JSON file operations (read, write, list JSON files)

ROUTING INSTRUCTIONS:
- For each user input, output ONLY the name of the agent to handle the request, exactly as one of: patient_agent, web_agent, text_agent, file_agent, json_agent.
- Do not output anything else. Do not invent new actions. Do not explain your choice.
- For greetings ("Hi", "Hello", etc.), general conversation, or if the user asks about available agents (e.g., "What agents do you have?"), output text_agent.
- For questions about patient info, medical data, personal details, names, age, medical history, output patient_agent.
- For current events, news, weather, online searches, factual questions ("who is", "what is"), output web_agent.
- For file operations ("read file", "write file", "Read example.txt"), output file_agent.
- For JSON file operations ("read json", "write json", "Read patient_profile.json"), output json_agent.
"""
        )
        
        # Setup session memory (InMemoryStore for current interaction)
        self.checkpointer = InMemorySaver()
        self.store = InMemoryStore()
        
        # Compile the workflow with session memory
        self.app = self.workflow.compile(
            checkpointer=self.checkpointer,
            store=self.store
        )
        
        logger.info("Supervisor workflow initialized successfully")

    def run(self, user_input: str) -> str:
        """Run the supervisor workflow with user input."""
        try:
            # Create initial state
            initial_state = {
                "messages": [
                    {"role": "user", "content": user_input}
                ]
            }
            
            # Create config with required checkpointer keys
            config = {
                "configurable": {
                    "thread_id": "default_thread",
                    "checkpoint_ns": "supervisor_workflow"
                }
            }
            
            # Run the workflow with proper config
            result = self.app.invoke(initial_state, config=config)
            
            if result is None:
                logger.error("Supervisor workflow returned None as result.")
                return "I apologize, but I encountered an internal error (no result)."
            
            # Debug: Print the result structure
            logger.info(f"Result keys: {list(result.keys())}")
            logger.info(f"Result type: {type(result)}")
            
            # Extract final response from messages
            messages = result.get("messages", [])
            logger.info(f"Messages count: {len(messages)}")
            logger.info(f"Messages: {messages}")
            
            final_response = None

            # Prefer explicit final_response from result if present and non-empty
            if result.get("final_response"):
                final_response = str(result["final_response"])
                logger.info(f"Using explicit final_response: {final_response[:100]}...")
            else:
                # Find the last assistant message with real content (not just agent/tool name)
                for message in reversed(messages):
                    # Handle both dict format and AIMessage objects
                    if isinstance(message, dict):
                        if (message.get("role") == "assistant" and message.get("content")):
                            content = message["content"].strip()
                            # Skip if content is just an agent/tool name
                            if not (content.endswith("_agent") and content.replace('_agent', '').isidentifier()):
                                final_response = content
                                logger.info(f"Found assistant message: {final_response[:100]}...")
                                break
                    elif hasattr(message, 'content') and hasattr(message, 'name'):
                        # Handle AIMessage objects
                        content = str(message.content).strip()
                        # Skip if content is just an agent/tool name or transfer messages
                        if (not content.endswith("_agent") and 
                            not content.startswith("Transferring") and
                            not content.startswith("Successfully") and
                            content):
                            final_response = content
                            logger.info(f"Found assistant message from {message.name}: {final_response[:100]}...")
                            break
            if not final_response:
                # Fallbacks
                if "next" in result:
                    final_response = str(result["next"])
                else:
                    final_response = "No response generated"

            logger.info(f"Supervisor workflow completed for input: {user_input[:50]}...")

            return final_response
            
        except Exception as e:
            logger.error(f"Error running supervisor workflow: {str(e)}")
            return f"I apologize, but I encountered an error: {str(e)}"

    def chat(self):
        """Start interactive chat session."""
        print("LangGraph Supervisor AI Agent is ready! Type 'quit' to exit.")
        print("You can:")
        print("- Ask questions about your patient profile")
        print("- Update your patient information")
        print("- Read/write files")
        print("- Search the web")
        print("- Summarize text")
        print("- Query the database")
        print()
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Get the full result dict (not just the final response)
                config = {
                    "configurable": {
                        "thread_id": "default_thread",
                        "checkpoint_ns": "supervisor_workflow"
                    }
                }
                result = self.app.invoke({"messages": [{"role": "user", "content": user_input}]}, config=config)
                messages = result.get("messages", [])
                print("\n--- Conversation Trace ---")
                for i, msg in enumerate(messages):
                    if isinstance(msg, dict):
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        print(f"{i+1}. {role}: {content}")
                    else:
                        print(f"{i+1}. {msg}")
                print("--- End Trace ---\n")
                # Optionally, still print the final response for convenience
                final_response = result.get("final_response")
                if final_response:
                    print(f"Agent (final response): {final_response}\n")
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")

def main():
    """Main function to run the supervisor workflow."""
    try:
        # Create necessary directories
        os.makedirs("data", exist_ok=True)
        os.makedirs("data/docs", exist_ok=True)
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Initialize and run supervisor workflow
        workflow = SupervisorWorkflow()
        workflow.chat()
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        print(f"Failed to start supervisor workflow: {str(e)}")

if __name__ == "__main__":
    main() 