# Main entry point for LangGraph Supervisor workflow

import os
from utils.logging_config import logger
from supervisor_workflow import SupervisorWorkflow

def main():
    """Main function to run the LangGraph Supervisor workflow."""
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