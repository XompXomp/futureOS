# Logging configuration 

import os
import logging
import sys
from datetime import datetime

def setup_logging():
    """Setup logging configuration for the application."""
    LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(LOGS_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(LOGS_DIR, f"agent_{datetime.now().strftime('%Y%m%d')}.log")),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()