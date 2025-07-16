# Logging configuration for LangGraph backend

import logging
import os
from datetime import datetime
from config.settings import settings

def setup_logging():
    """Setup logging configuration for the LangGraph backend."""
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.WARNING),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(logs_dir, f"langgraph_{datetime.now().strftime('%Y%m%d')}.log")),
            logging.StreamHandler()
        ]
    )
    
    # Create logger
    logger = logging.getLogger("langgraph_backend")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.WARNING))
    
    return logger

# Initialize logger
logger = setup_logging() 