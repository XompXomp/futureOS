# JSON manipulation operations 

import json
import re
from typing import Dict, Any, Optional
from modules.file_operations import FileOperations
from utils.logging_config import logger
import openai
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from config.settings import settings
import json
import os

class JSONOperations:
    @staticmethod
    def _validate_docs_path(file_path: str) -> bool:
        """Ensure the file path is within the allowed docs directory."""
        abs_docs = os.path.abspath(settings.DOCS_FOLDER)
        abs_file = os.path.abspath(file_path)
        return abs_file.startswith(abs_docs)

    @staticmethod
    def load_json_from_file(file_path: str) -> Optional[Dict[str, Any]]:
        """Load JSON data from a file (restricted to docs folder)."""
        if not JSONOperations._validate_docs_path(file_path):
            logger.error(f"Access denied: {file_path} is outside the allowed docs directory.")
            return None
        try:
            if settings.VERBOSE:
                print(f"[DEBUG] Loading JSON from file: {file_path}")
            content = FileOperations.read_file(file_path)
            if content is None:
                return None
            
            # Parse JSON
            json_data = json.loads(content)
            if settings.VERBOSE:
                print(f"[DEBUG] Loaded JSON data: {json_data}")
            logger.info(f"Successfully loaded JSON from: {file_path}")
            return json_data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {file_path}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error loading JSON from file {file_path}: {str(e)}")
            return None

    @staticmethod
    def save_json_to_file(file_path: str, data: Dict[str, Any]) -> bool:
        """Save JSON data to a file (restricted to docs folder)."""
        if not JSONOperations._validate_docs_path(file_path):
            logger.error(f"Access denied: {file_path} is outside the allowed docs directory.")
            return False
        try:
            if settings.VERBOSE:
                print(f"[DEBUG] Saving JSON to file: {file_path}")
                print(f"[DEBUG] Data to save: {data}")
            json_content = json.dumps(data, indent=2, ensure_ascii=False)
            result = FileOperations.write_file(file_path, json_content)
            if settings.VERBOSE:
                print(f"[DEBUG] Write file result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error saving JSON to file {file_path}: {str(e)}")
            return False

    @staticmethod
    def update_json_values(file_path: str, updates: Dict[str, Any]) -> bool:
        """Update specific values in a JSON file while preserving structure (restricted to docs folder)."""
        if not JSONOperations._validate_docs_path(file_path):
            logger.error(f"Access denied: {file_path} is outside the allowed docs directory.")
            return False
        try:
            # Load existing JSON
            json_data = JSONOperations.load_json_from_file(file_path)
            if json_data is None:
                logger.error(f"Could not load JSON from {file_path}")
                return False
            
            # Update values recursively
            JSONOperations._update_nested_dict(json_data, updates)
            
            # Save updated JSON
            success = JSONOperations.save_json_to_file(file_path, json_data)
            if success:
                logger.info(f"Successfully updated JSON values in: {file_path}")
            return success
        except Exception as e:
            logger.error(f"Error updating JSON values in {file_path}: {str(e)}")
            return False

    @staticmethod
    def _update_nested_dict(original: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """Recursively update nested dictionary values."""
        for key, value in updates.items():
            if key in original:
                if isinstance(original[key], dict) and isinstance(value, dict):
                    JSONOperations._update_nested_dict(original[key], value)
                else:
                    original[key] = value
            else:
                # If key doesn't exist, add it
                original[key] = value

    @staticmethod
    def update_json_with_llm(current_json: dict, user_request: str) -> dict:
        """Use Ollama or Groq via LangChain to update the JSON based on a user request."""
        if not isinstance(current_json, str):
            current_json_str = json.dumps(current_json, indent=2)
        else:
            current_json_str = current_json
        prompt = f"""
You are a precise assistant for updating JSON data. Your job is to take the full JSON object below, update ONLY the field(s) relevant to the user's request, and return the ENTIRE JSON in the exact same structure and format as provided. Do not change, add, or remove any other fields or values. Do not invent or hallucinate new information. If the request is ambiguous, make no changes and return the original JSON.

Current JSON:
{current_json_str}

User request: "{user_request}"

Return ONLY the full, updated JSON. Do not include any explanation, comments, or extra text. Do not change the structure or formatting of the JSON except for the requested update.
"""
        if settings.VERBOSE:
            print(f"[DEBUG] update_json_with_llm prompt:\n{prompt}")
        # Select LLM based on settings
        if settings.USE_OLLAMA:
            llm = ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0
            )
        else:
            llm = ChatGroq(
                model=settings.LLM_MODEL,
                temperature=0
            )
        response = llm.invoke(prompt)
        if settings.VERBOSE:
            print(f"[DEBUG] LLM raw response: {response}")
        # Handle response type: string, list, or object with 'content'
        if hasattr(response, 'content'):
            content = str(response.content)
        elif isinstance(response, list):
            # Join all string parts if it's a list
            content = ''.join([str(part) for part in response])
        else:
            content = str(response)
        content = content.strip()
        if settings.VERBOSE:
            print(f"[DEBUG] LLM content to parse as JSON: {content}")
        try:
            updated_json = json.loads(content)
        except json.JSONDecodeError:
            import re
            match = re.search(r'({.*})', content, re.DOTALL)
            if match:
                updated_json = json.loads(match.group(1))
            else:
                raise ValueError("LLM did not return valid JSON:\n" + content)
        return updated_json

    @staticmethod
    def extract_json_updates_from_text(text: str) -> dict:
        """Deprecated: Use update_json_with_llm instead."""
        raise NotImplementedError("Use update_json_with_llm instead.")