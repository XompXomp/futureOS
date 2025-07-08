# JSON manipulation operations 

import json
import re
from typing import Dict, Any, Optional
from modules.file_operations import FileOperations
from utils.logging_config import logger

class JSONOperations:
    @staticmethod
    def load_json_from_file(file_path: str) -> Optional[Dict[str, Any]]:
        """Load JSON data from a file."""
        try:
            content = FileOperations.read_file(file_path)
            if content is None:
                return None
            
            # Parse JSON
            json_data = json.loads(content)
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
        """Save JSON data to a file."""
        try:
            json_content = json.dumps(data, indent=2, ensure_ascii=False)
            return FileOperations.write_file(file_path, json_content)
        except Exception as e:
            logger.error(f"Error saving JSON to file {file_path}: {str(e)}")
            return False

    @staticmethod
    def update_json_values(file_path: str, updates: Dict[str, Any]) -> bool:
        """Update specific values in a JSON file while preserving structure."""
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
    def extract_json_updates_from_text(text: str) -> Dict[str, Any]:
        """Extract JSON updates from natural language text."""
        updates = {}
        
        # Pattern matching for common update patterns
        patterns = [
            (r"(?:my )?age.*?(\d+)", "age"),
            (r"(?:my )?name\s+(?:is\s+)?([A-Za-z\s]+?)(?:\s|$|\.|,)", "name"),
            (r"(?:my )?weight.*?(\d+(?:\.\d+)?)", "weight"),
            (r"(?:my )?height.*?(\d+(?:\.\d+)?)", "height"),
            (r"(?:my )?phone.*?(\+?[\d\s\-\(\)]+)", "phone"),
            (r"(?:my )?email.*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", "email"),
            # Medical patterns
            (r"(?:my )?blood\s+type.*?([A-Za-z]+)", "blood_type"),
            (r"(?:my )?allergies.*?([A-Za-z\s,]+?)(?:\s|$|\.|,)", "allergies"),
            (r"(?:my )?medications.*?([A-Za-z0-9\s,]+?)(?:\s|$|\.|,)", "current_medications"),
            (r"(?:my )?chronic\s+conditions.*?([A-Za-z\s,]+?)(?:\s|$|\.|,)", "chronic_conditions"),
            # Medication specific patterns
            (r"(?:taking|on|prescribed)\s+(\d+mg?\s+[A-Za-z]+)", "current_medications"),
            (r"(\d+mg?\s+[A-Za-z]+)\s+(?:at|for|to)", "current_medications"),
        ]
        
        for pattern, field in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Clean up the value
                if field == "name":
                    # Remove common words that shouldn't be part of the name
                    value = re.sub(r'\b(is|am|are|the|a|an)\b', '', value, flags=re.IGNORECASE).strip()
                    # Remove extra whitespace
                    value = ' '.join(value.split())
                elif field in ["allergies", "current_medications", "chronic_conditions"]:
                    # Handle array fields - split by comma and clean up
                    if isinstance(value, str):
                        value = [item.strip() for item in value.split(',') if item.strip()]
                    else:
                        value = [str(value)]
                # Convert to appropriate type (only for numeric fields)
                elif field in ["age", "weight", "height"]:
                    try:
                        value = float(value) if '.' in value else int(value)
                    except:
                        pass
                updates[field] = value
        
        # Add pattern for goals
        goal_patterns = [
            r"(?:add|my|new)?\s*goal(?: is|:)?\s*['\"]?(.+?)(?:['\"]|$|\.)",
            r"goal to (.+?)(?:\\.|$)",
            r"reach (\d+\s*steps?)\s*(?:every day|daily)"
        ]
        for pattern in goal_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                goal = match.group(1).strip()
                updates.setdefault("goals", []).append(goal)
        
        return updates