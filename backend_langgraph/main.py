# Main entry point for LangGraph Supervisor workflow

import os
from utils.logging_config import logger
from supervisor_workflow import EnhancedSupervisorWorkflow
from config.settings import settings

def main():
    """Main function to run the Enhanced LangGraph Supervisor workflow."""
    try:
        # Create necessary directories
        os.makedirs("data", exist_ok=True)
        os.makedirs("data/docs", exist_ok=True)
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Initialize and run supervisor workflow
        workflow = EnhancedSupervisorWorkflow()
        workflow.chat()
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        if settings.DEBUG:
            print(f"Failed to start enhanced supervisor workflow: {str(e)}")

if __name__ == "__main__":
    main() 