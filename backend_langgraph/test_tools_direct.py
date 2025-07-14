#!/usr/bin/env python3
"""Test tools directly to verify they work."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.web_search_tools import search_web
from tools.text_tools import summarize_text, extract_keywords
from tools.json_tools import list_json_files
from tools.file_tools import read_file
from tools.patient_tools import read_patient_profile
from tools.memory_tools import create_memory_tools

def test_tools():
    """Test various tools directly."""
    print("Testing tools directly...")
    
    # Test state
    state = {
        "user_input": "test",
        "messages": [],
        "tool_results": []
    }
    
    # Test web search
    print("\n1. Testing web search...")
    try:
        web_result = search_web(state)
        print(f"Web search state keys: {list(web_result.keys())}")
        print(f"Web search message: {web_result.get('search_message', 'No message')}")
        print(f"Web search results: {len(web_result.get('search_results', []))} results")
    except Exception as e:
        print(f"Web search error: {e}")
    
    # Test text tools
    print("\n2. Testing text tools...")
    try:
        text_state = state.copy()
        text_state["user_input"] = "This is a test text for summarization and keyword extraction."
        summary_result = summarize_text(text_state)
        print(f"Summarize state keys: {list(summary_result.keys())}")
        print(f"Summarize text: {summary_result.get('text_summary', 'No summary')}")
        
        keyword_result = extract_keywords(text_state)
        print(f"Keywords state keys: {list(keyword_result.keys())}")
        print(f"Keywords: {keyword_result.get('keywords', 'No keywords')}")
    except Exception as e:
        print(f"Text tools error: {e}")
    
    # Test JSON tools
    print("\n3. Testing JSON tools...")
    try:
        json_result = list_json_files(state)
        print(f"JSON state keys: {list(json_result.keys())}")
        print(f"JSON files: {json_result.get('json_files', 'No files')}")
    except Exception as e:
        print(f"JSON tools error: {e}")
    
    # Test file tools
    print("\n4. Testing file tools...")
    try:
        file_state = state.copy()
        file_state["file_path"] = "data/docs/example.txt"
        file_result = read_file(file_state)
        print(f"File state keys: {list(file_result.keys())}")
        print(f"File content: {file_result.get('file_content', 'No content')[:100]}...")
    except Exception as e:
        print(f"File tools error: {e}")
    
    # Test patient tools
    print("\n5. Testing patient tools...")
    try:
        patient_result = read_patient_profile(state)
        print(f"Patient state keys: {list(patient_result.keys())}")
        print(f"Patient profile: {patient_result.get('patient_profile', 'No profile')}")
    except Exception as e:
        print(f"Patient tools error: {e}")
    
    # Test memory tools
    print("\n6. Testing memory tools...")
    try:
        memory_tools = create_memory_tools("test_agent")
        print(f"Memory tools created: {[tool.__name__ for tool in memory_tools]}")
        
        # Test semantic memory
        memory_state = state.copy()
        memory_state["user_input"] = "Store this test information"
        memory_state["content"] = "This is test information for semantic memory"
        memory_state["category"] = "test"
        
        # Try to call the first memory tool
        if memory_tools:
            first_tool = memory_tools[0]
            memory_result = first_tool(memory_state)
            print(f"Memory state keys: {list(memory_result.keys())}")
            print(f"Memory result: {memory_result.get('memory_id', 'No memory ID')}")
    except Exception as e:
        print(f"Memory tools error: {e}")

if __name__ == "__main__":
    test_tools() 