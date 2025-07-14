#!/usr/bin/env python3
"""Test script for JSON agent."""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from config.settings import settings
from tools.json_tools import read_json_file, write_json_file, list_json_files

def test_json_agent():
    """Test the JSON agent directly."""
    print("Testing JSON agent...")
    
    # Initialize LLM
    if settings.USE_OLLAMA:
        model = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.3
        )
    else:
        model = ChatGroq(
            model=settings.LLM_MODEL,
            temperature=0.3
        )
    
    # Create JSON agent with only core tools (no memory)
    json_agent = create_react_agent(
        model=model,
        tools=[read_json_file, write_json_file, list_json_files],
        name="json_agent",
        prompt="""You are a JSON file management agent with access to JSON file operations.

AVAILABLE TOOLS:
- read_json_file: Read JSON files from the data/docs directory
- write_json_file: Write JSON data to files in the data/docs directory
- list_json_files: List all JSON files in the data/docs directory

INSTRUCTIONS:
1. When asked to read JSON files → Use read_json_file tool
2. When asked to write JSON files → Use write_json_file tool
3. When asked to list JSON files → Use list_json_files tool
4. The default directory for JSON operations is data/docs
5. Be conversational and helpful with JSON-related queries

EXAMPLES:
- User: "Read patient_profile.json" → Use read_json_file tool
- User: "List all JSON files" → Use list_json_files tool
- User: "Write data to config.json" → Use write_json_file tool"""
    )
    
    print(f"Created JSON agent: {json_agent}")
    
    # Test cases
    test_cases = [
        "List all JSON files",
        "Read patient_profile.json",
        "What JSON files are available?",
        "Read test.json",
        "Write {'name': 'John', 'age': 30} to user.json"
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_input} ---")
        
        # Create test state
        test_state = {
            "messages": [
                {"role": "user", "content": test_input}
            ]
        }
        
        try:
            # Call the agent
            result = json_agent.invoke(test_state)
            print(f"Result: {result}")
            
            # Extract the response
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    response = last_message.content
                elif isinstance(last_message, dict):
                    response = last_message.get("content", "No content")
                else:
                    response = str(last_message)
                print(f"Response: {response}")
            else:
                print("No messages in result")
                
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_json_agent() 