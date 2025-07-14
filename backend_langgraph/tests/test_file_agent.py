#!/usr/bin/env python3
"""Test script for file agent."""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from config.settings import settings
from tools.file_tools import read_file, write_file

def test_file_agent():
    """Test the file agent directly."""
    print("Testing file agent...")
    
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
    
    # Create file agent with only core tools (no memory)
    file_agent = create_react_agent(
        model=model,
        tools=[read_file, write_file],
        name="file_agent",
        prompt="""You are a file management agent with access to file operations.

AVAILABLE TOOLS:
- read_file: Read files from the data/docs directory
- write_file: Write content to files in the data/docs directory

INSTRUCTIONS:
1. When asked to read files → Use read_file tool
2. When asked to write files → Use write_file tool
3. The default directory for file operations is data/docs
4. Be conversational and helpful with file-related queries

EXAMPLES:
- User: "Read example.txt" → Use read_file tool
- User: "Write 'Hello World' to test.txt" → Use write_file tool"""
    )
    
    print(f"Created file agent: {file_agent}")
    
    # Test cases
    test_cases = [
        "Read example.txt",
        "Write 'Hello World' to test.txt",
        "What files are available?",
        "Read test.txt",
        "Write 'This is a test file' to sample.txt"
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
            result = file_agent.invoke(test_state)
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
    test_file_agent() 