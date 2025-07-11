# Main entry point for LangGraph backend

import os
from typing import Dict, Any
from langgraph.graph import StateGraph
from utils.logging_config import logger
from config.settings import settings
from state.schema import PatientState
from graph.patient_graph import create_patient_graph, create_initial_state

class LangGraphAgent:
    def __init__(self):
        """Initialize the LangGraph agent."""
        try:
            # Create the workflow graph
            self.graph = create_patient_graph()
            self.app = self.graph.compile()
            
            logger.info("LangGraph agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing LangGraph agent: {str(e)}")
            raise

    def run(self, user_input: str) -> str:
        """Run the LangGraph workflow with user input."""
        try:
            # Create initial state
            initial_state = create_initial_state(user_input)
            
            # Run the workflow
            result = self.app.invoke(initial_state)
            if result is None:
                logger.error("LangGraph workflow returned None as result.")
                return "I apologize, but I encountered an internal error (no result)."
            
            # Extract final response
            final_response = result.get("final_response", "No response generated")
            
            logger.info(f"LangGraph workflow completed for input: {user_input[:50]}...")
            
            return final_response
            
        except Exception as e:
            logger.error(f"Error running LangGraph workflow: {str(e)}")
            return f"I apologize, but I encountered an error: {str(e)}"

    def chat(self):
        """Start interactive chat session."""
        print("LangGraph AI Agent is ready! Type 'quit' to exit.")
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
                
                response = self.run(user_input)
                print(f"\nAgent: {response}")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")

def main():
    """Main function to run the LangGraph agent."""
    try:
        # Create necessary directories
        os.makedirs("data", exist_ok=True)
        os.makedirs("data/docs", exist_ok=True)
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Initialize and run agent
        agent = LangGraphAgent()
        agent.chat()
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        print(f"Failed to start LangGraph agent: {str(e)}")

if __name__ == "__main__":
    main() 