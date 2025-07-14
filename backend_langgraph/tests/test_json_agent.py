#!/usr/bin/env python3
"""
Test script specifically for the JSON agent.
Tests JSON file reading, writing, and listing operations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.json_agent import JsonAgent
from utils.logging_config import logger

def test_json_agent():
    """Test the JSON agent with various JSON file operations."""
    print("\n" + "="*60)
    print("TESTING JSON AGENT - DETAILED ANALYSIS")
    print("="*60)
    
    agent = JsonAgent()
    
    # Test 1: List JSON files
    print("\n--- TEST 1: List JSON files ---")
    state = {
        'user_input': "List JSON files",
        'messages': [{'role': 'user', 'content': "List JSON files"}],
        'patient_profile': {},
        'profile_updated': False,
        'tool_results': [],
        'current_tool': None,
        'should_continue': True,
        'iteration_count': 0,
        'max_iterations': 5,
        'error_message': None,
        'has_error': False,
        'final_response': None,
        'response_generated': False
    }
    
    try:
        result = agent.handle(state)
        print(f"Response: {result.get('final_response', 'No response')}")
        if result.get('has_error'):
            print(f"Error: {result.get('error_message')}")
    except Exception as e:
        print(f"Exception: {str(e)}")
    
    # Test 2: Read a JSON file
    print("\n--- TEST 2: Read patient_profile.json ---")
    state = {
        'user_input': "Read patient_profile.json",
        'messages': [{'role': 'user', 'content': "Read patient_profile.json"}],
        'file_path': "patient_profile.json",
        'patient_profile': {},
        'profile_updated': False,
        'tool_results': [],
        'current_tool': None,
        'should_continue': True,
        'iteration_count': 0,
        'max_iterations': 5,
        'error_message': None,
        'has_error': False,
        'final_response': None,
        'response_generated': False
    }
    
    try:
        result = agent.handle(state)
        print(f"Response: {result.get('final_response', 'No response')}")
        if result.get('has_error'):
            print(f"Error: {result.get('error_message')}")
    except Exception as e:
        print(f"Exception: {str(e)}")
    
    # Test 3: Write a JSON file
    print("\n--- TEST 3: Write test data to test.json ---")
    test_data = {
        "test": "data",
        "number": 42,
        "list": [1, 2, 3]
    }
    state = {
        'user_input': "Write test data to test.json",
        'messages': [{'role': 'user', 'content': "Write test data to test.json"}],
        'file_path': "test.json",
        'data': test_data,
        'patient_profile': {},
        'profile_updated': False,
        'tool_results': [],
        'current_tool': None,
        'should_continue': True,
        'iteration_count': 0,
        'max_iterations': 5,
        'error_message': None,
        'has_error': False,
        'final_response': None,
        'response_generated': False
    }
    
    try:
        result = agent.handle(state)
        print(f"Response: {result.get('final_response', 'No response')}")
        if result.get('has_error'):
            print(f"Error: {result.get('error_message')}")
    except Exception as e:
        print(f"Exception: {str(e)}")
    
    # Test 4: Read the file we just wrote
    print("\n--- TEST 4: Read test.json (verify write worked) ---")
    state = {
        'user_input': "Read test.json",
        'messages': [{'role': 'user', 'content': "Read test.json"}],
        'file_path': "test.json",
        'patient_profile': {},
        'profile_updated': False,
        'tool_results': [],
        'current_tool': None,
        'should_continue': True,
        'iteration_count': 0,
        'max_iterations': 5,
        'error_message': None,
        'has_error': False,
        'final_response': None,
        'response_generated': False
    }
    
    try:
        result = agent.handle(state)
        print(f"Response: {result.get('final_response', 'No response')}")
        if result.get('has_error'):
            print(f"Error: {result.get('error_message')}")
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    test_json_agent() 