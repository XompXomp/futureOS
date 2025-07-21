# Main agent orchestrator 

import os
from langchain.agents import initialize_agent, AgentType
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain.memory import ConversationBufferWindowMemory
from config.settings import settings
from tools.patient_tools import create_patient_tools
from tools.text_tools import create_text_tools
from tools.web_tools import create_web_tools
from tools.memory_tools import create_memory_tools
from utils.logging_config import logger
import json
from typing import Optional, Any
from dotenv import load_dotenv
load_dotenv()  # This will load .env into os.environ

class AIAgent:
    def __init__(self):
        self.agent: Optional[Any] = None
        if settings.USE_OLLAMA:
            self.llm = ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.3
            )
        elif settings.USE_GROQ:
            self.llm = ChatGroq(
                model=settings.LLM_MODEL,
                temperature=0.3
            )
        else:
            raise ValueError("Invalid LLM_PROVIDER. Set LLM_PROVIDER to 'ollama' or 'groq'.")
        self.memory = ConversationBufferWindowMemory(
           memory_key="chat_history",
           return_messages=True,
           k=10
        )
        self.agent = None
        self.setup_agent()
        # No patient profile file initialization

    def setup_agent(self):
        """Setup the AI agent with all tools."""
        try:
            # Collect all tools
            all_tools = []
            all_tools.extend(create_patient_tools())
            all_tools.extend(create_text_tools())
            all_tools.extend(create_web_tools())
            all_tools.extend(create_memory_tools())
            
            # Initialize agent
            self.agent = initialize_agent(
                tools=all_tools,
                llm=self.llm,
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                memory=self.memory,
                verbose=settings.VERBOSE,
                max_iterations=settings.MAX_ITERATIONS,
                handle_parsing_errors=True,
                agent_kwargs={
                    "system_message": """You are a helpful AI assistant for a patient management system. 
                    
                    IMPORTANT CONTEXT:
                    - When the user says \"I\", \"me\", \"my\", \"myself\" - they are referring to THEMSELVES as the PATIENT
                    - When the user asks about \"my name\", \"my age\", \"my medical info\" - they want information about THEMSELVES (the patient)
                    - You should treat \"I\" and \"patient\" as the same person
                    - Always check the patient profile when users ask about themselves
                    - Use the read_patient_profile tool when users ask about their information
                    - Use the update_patient_profile tool when users want to update their information
                    
                    CRITICAL INSTRUCTIONS:
                    - After using a tool and receiving the requested information, ALWAYS provide a clear, direct answer to the user
                    - Do NOT keep calling the same tool repeatedly with the same input
                    - If you receive the information you need, stop using tools and give the user their answer
                    - Format your final response in a helpful, conversational way
                    
                    Your role is to help patients manage their information and answer questions about their health records."""
                }
            )
            
            logger.info(f"Agent initialized with {len(all_tools)} tools")
        except Exception as e:
            logger.error(f"Error setting up agent: {str(e)}")
            raise

    def run(self, user_input: str, memory: dict = None, patient_profile: dict = None) -> dict:
        """Run the agent with user input, memory, and patient_profile as dicts. Pass them to every tool operation and capture updates."""
        try:
            if self.agent is None:
                logger.error("Agent is not initialized.")
                return {"error": "Agent is not initialized.", "memory": memory, "patient_profile": patient_profile}

            # Custom tool-calling wrapper to inject memory/patient_profile
            def tool_wrapper(tool_func):
                def wrapped(*args, **kwargs):
                    if args and isinstance(args[0], dict):
                        state = args[0]
                    else:
                        state = {}
                    if memory is not None:
                        state['memory'] = memory
                    if patient_profile is not None:
                        state['patientProfile'] = patient_profile
                    result = tool_func(state)
                    # No nonlocal; just return the updated state
                    return result
                return wrapped

            # Patch all tools to use the wrapper
            for tool in self.agent.tools:
                tool.func = tool_wrapper(tool.func)

            state = self.agent.run(user_input)
            # After agent.run, extract updated memory and patient_profile from state
            if isinstance(state, dict):
                memory = state.get('memory', memory)
                patient_profile = state.get('patientProfile', patient_profile)
            logger.info(f"Agent response generated for input: {user_input[:50]}...")
            return {"response": state, "memory": memory, "patient_profile": patient_profile}
        except Exception as e:
            logger.error(f"Error running agent: {str(e)}")
            return {"error": f"I apologize, but I encountered an error: {str(e)}", "memory": memory, "patient_profile": patient_profile}

    def chat(self):
        """Start interactive chat session with in-memory memory and patient_profile dicts."""
        print("AI Agent is ready! Type 'quit' to exit.")
        print("You can:")
        print("- Ask questions about your patient profile")
        print("- Summarize text or extract keywords")
        print("- Search the web for information")
        print("- Store and search semantic memory")
        print()
        memory = {"semantic": [], "episodes": [], "procedural": {}}
        patient_profile = {}  # Start with empty dict, never read from disk
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("Goodbye!")
                    break
                if not user_input:
                    continue
                result = self.run(user_input, memory=memory, patient_profile=patient_profile)
                memory = result.get("memory", memory)
                patient_profile = result.get("patient_profile", patient_profile)
                if "response" in result:
                    print(f"\nAgent: {result['response']}")
                elif "error" in result:
                    print(f"\nAgent (error): {result['error']}")
                else:
                    print(f"\nAgent: (no response)")
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")

def main():
    """Main function to run the AI agent."""
    try:
        LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "utils", "logs")
        os.makedirs(LOGS_DIR, exist_ok=True)
        agent = AIAgent()
        agent.chat()
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        print(f"Failed to start agent: {str(e)}")

if __name__ == "__main__":
    main()
