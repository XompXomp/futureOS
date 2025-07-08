# Logging configuration 

import os
import logging
import sys
from datetime import datetime

def setup_logging():
    """Setup logging configuration for the application."""
    # Ensure the logs directory exists
    os.makedirs("backend/logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(f"backend/logs/agent_{datetime.now().strftime('%Y%m%d')}.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()