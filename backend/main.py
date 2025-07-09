# Main agent orchestrator 

import os
from langchain.agents import initialize_agent, AgentType
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain.memory import ConversationBufferWindowMemory
from config.settings import settings
from tools.file_tools import create_file_tools
from tools.json_tools import create_json_tools
from tools.text_tools import create_text_tools
from tools.database_tools import create_database_tools
from tools.rag_tools import create_rag_tools
from tools.google_pse_tools import create_google_pse_tools
from utils.logging_config import logger
from modules.file_operations import FileOperations
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
        else:
            self.llm = ChatGroq(
                model=settings.LLM_MODEL,
                temperature=0.3
            )
        self.memory = ConversationBufferWindowMemory(
           memory_key="chat_history",
           return_messages=True,
           k=10
        )
        self.agent = None
        self.setup_agent()
        self.initialize_patient_profile()

    def setup_agent(self):
        """Setup the AI agent with all tools."""
        try:
            # Collect all tools
            all_tools = []
            all_tools.extend(create_file_tools()) # File operations
            all_tools.extend(create_json_tools()) # JSON operations
            all_tools.extend(create_text_tools()) # Text operations
            all_tools.extend(create_database_tools()) # Database operations
            all_tools.extend(create_rag_tools()) # RAG operations
            all_tools.extend(create_google_pse_tools()) # Google PSE operations
            
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
                    - When the user says "I", "me", "my", "myself" - they are referring to THEMSELVES as the PATIENT
                    - When the user asks about "my name", "my age", "my medical info" - they want information about THEMSELVES (the patient)
                    - You should treat "I" and "patient" as the same person
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

    def initialize_patient_profile(self):
        """Initialize patient profile with default structure if it doesn't exist."""
        try:
            default_profile = {
                "personal_info": {
                    "name": "",
                    "age": 0,
                    "gender": "",
                    "phone": "",
                    "email": "",
                    "address": ""
                },
                "medical_info": {
                    "height": 0,
                    "weight": 0,
                    "blood_type": "",
                    "allergies": [],
                    "chronic_conditions": [],
                    "current_medications": []
                },
                "emergency_contact": {
                    "name": "",
                    "relationship": "",
                    "phone": ""
                },
                "insurance": {
                    "provider": "",
                    "policy_number": "",
                    "group_number": ""
                }
            }
            
            # Create the profile file if it doesn't exist
            if not FileOperations.file_exists(settings.PATIENT_PROFILE_PATH):
                profile_content = json.dumps(default_profile, indent=2)
                success = FileOperations.write_file(settings.PATIENT_PROFILE_PATH, profile_content)
                if success:
                    logger.info("Default patient profile created")
                else:
                    logger.error("Could not create default patient profile")
            
        except Exception as e:
            logger.error(f"Error initializing patient profile: {str(e)}")

    def run(self, user_input: str) -> str:
        """Run the agent with user input."""
        try:
            if self.agent is None:
                logger.error("Agent is not initialized.")
                return "Agent is not initialized."
            
            # Check if we're hitting rate limits too frequently
            if hasattr(self, '_rate_limit_count'):
                self._rate_limit_count += 1
            else:
                self._rate_limit_count = 0
            
            if self._rate_limit_count > 3:
                return "I'm experiencing high demand right now. Please try again in a few minutes or switch to local mode (Ollama)."
            
            response = self.agent.run(user_input)
            # Reset rate limit counter on success
            self._rate_limit_count = 0
            logger.info(f"Agent response generated for input: {user_input[:50]}...")
            return response
        except Exception as e:
            logger.error(f"Error running agent: {str(e)}")
            if "rate limit" in str(e).lower() or "429" in str(e):
                self._rate_limit_count = getattr(self, '_rate_limit_count', 0) + 1
                return f"Rate limit reached. Please try again later or switch to local mode."
            return f"I apologize, but I encountered an error: {str(e)}"

    def chat(self):
        """Start interactive chat session."""
        print("AI Agent is ready! Type 'quit' to exit.")
        print("You can:")
        print("- Ask questions about documents")
        print("- Query the database")
        print("- Update your patient profile")
        print("- Read/write files")
        print("- Summarize text")
        print()
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                response = self.run(user_input)
                print(f"\nAgent: {response}")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")

def main():
    """Main function to run the AI agent."""
    try:
        # Create necessary directories
        os.makedirs("data", exist_ok=True)
        os.makedirs("data/docs", exist_ok=True)
        LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "utils", "logs")
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        # Initialize and run agent
        agent = AIAgent()
        agent.chat()
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        print(f"Failed to start agent: {str(e)}")

if __name__ == "__main__":
    main()
