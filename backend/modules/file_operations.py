# File read/write operations 

import os
from typing import Optional
from utils.logging_config import logger

class FileOperations:
    @staticmethod
    def read_file(file_path: str) -> Optional[str]:
        """Read content from a text file."""
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            logger.info(f"Successfully read file: {file_path}")
            return content
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return None

    @staticmethod
    def write_file(file_path: str, content: str, overwrite: bool = True) -> bool:
        """Write content to a text file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            mode = 'w' if overwrite else 'x'
            with open(file_path, mode, encoding='utf-8') as file:
                file.write(content)
            
            logger.info(f"Successfully wrote to file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error writing to file {file_path}: {str(e)}")
            return False

    @staticmethod
    def append_to_file(file_path: str, content: str) -> bool:
        """Append content to a text file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'a', encoding='utf-8') as file:
                file.write(content)
            
            logger.info(f"Successfully appended to file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error appending to file {file_path}: {str(e)}")
            return False

    @staticmethod
    def file_exists(file_path: str) -> bool:
        """Check if a file exists."""
        return os.path.exists(file_path)

    @staticmethod
    def create_file_if_not_exists(file_path: str, default_content: str = "") -> bool:
        """Create a file with default content if it doesn't exist."""
        if not FileOperations.file_exists(file_path):
            return FileOperations.write_file(file_path, default_content)
        return True