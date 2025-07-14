#!/usr/bin/env python3
"""
Test script specifically for the patient agent.
Tests patient profile reading, name queries, and profile updates.
Shows memory contents after each operation to verify storage.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.patient_agent import PatientAgent
from utils.logging_config import logger
from langchain_core.messages import HumanMessage

def show_memory_contents(agent, test_name):
    """Show what's currently stored in the agent's semantic memory"""
    print(f"\n🔍 MEMORY CONTENTS AFTER {test_name}:")
    print("-" * 50)
    
    try:
        # Get all namespaces
        all_namespaces = agent.store.list_namespaces()
        print(f"Total Namespaces: {len(all_namespaces)}")
        for ns in all_namespaces:
            print(f"  - {ns}")
        
        print("\n📋 Items in each namespace:")
        
        # Check profile namespace memory
        try:
            profile_items = agent.store.search(agent.profile_namespace, limit=1000)
            print(f"\nProfile Memory Items ({agent.profile_namespace}): {len(profile_items)}")
            for item in profile_items:
                print(f"  - Key: {item.key}")
                print(f"    Content: {item.value}")
                print(f"    Created: {item.created_at}")
                print(f"    Updated: {item.updated_at}")
                print()
        except Exception as e:
            print(f"Error accessing profile memory: {str(e)}")
        
        # Check episodic namespace memory
        try:
            episodic_items = agent.store.search(agent.episodic_namespace, limit=1000)
            print(f"\nEpisodic Memory Items ({agent.episodic_namespace}): {len(episodic_items)}")
            for item in episodic_items:
                print(f"  - Key: {item.key}")
                print(f"    Content: {item.value}")
                print(f"    Created: {item.created_at}")
                print(f"    Updated: {item.updated_at}")
                print()
        except Exception as e:
            print(f"Error accessing episodic memory: {str(e)}")
        
        # Check procedural namespace memory
        try:
            procedural_items = agent.store.search(agent.procedural_namespace, limit=1000)
            print(f"\nProcedural Memory Items ({agent.procedural_namespace}): {len(procedural_items)}")
            for item in procedural_items:
                print(f"  - Key: {item.key}")
                print(f"    Content: {item.value}")
                print(f"    Created: {item.created_at}")
                print(f"    Updated: {item.updated_at}")
                print()
        except Exception as e:
            print(f"Error accessing procedural memory: {str(e)}")
            
    except Exception as e:
        print(f"Error accessing memory: {str(e)}")

def test_patient_agent():
    """Test the patient agent with specific queries and show memory contents."""
    print("\n" + "="*60)
    print("TESTING PATIENT AGENT - DETAILED ANALYSIS WITH MEMORY INSPECTION")
    print("="*60)
    
    agent = PatientAgent()
    
    # Test 1: Basic name query
    print("\n--- TEST 1: What is my name? ---")
    state = {
        'user_input': "What is my name?",
        'messages': [HumanMessage(content="What is my name?")],
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
    
    show_memory_contents(agent, "TEST 1")
    
    # Test 2: Store patient information
    print("\n--- TEST 2: Store patient information ---")
    state = {
        'user_input': "My name is John Smith, I'm 30 years old, and I have diabetes",
        'messages': [HumanMessage(content="My name is John Smith, I'm 30 years old, and I have diabetes")],
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
    
    show_memory_contents(agent, "TEST 2")
    
    # Test 3: Query stored information
    print("\n--- TEST 3: What is my name? (after storing) ---")
    state = {
        'user_input': "What is my name?",
        'messages': [HumanMessage(content="What is my name?")],
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
    
    show_memory_contents(agent, "TEST 3")
    
    # Test 4: Update age to 35
    print("\n--- TEST 4: Update my age to 35 ---")
    state = {
        'user_input': "Update my age to 35",
        'messages': [HumanMessage(content="Update my age to 35")],
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
    
    show_memory_contents(agent, "TEST 4")
    
    # Test 5: Check if age was actually updated
    print("\n--- TEST 5: What is my age? (after update) ---")
    state = {
        'user_input': "What is my age?",
        'messages': [HumanMessage(content="What is my age?")],
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
    
    show_memory_contents(agent, "TEST 5")
    
    # Test 6: Query medical conditions
    print("\n--- TEST 6: What medical conditions do I have? ---")
    state = {
        'user_input': "What medical conditions do I have?",
        'messages': [HumanMessage(content="What medical conditions do I have?")],
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
    
    show_memory_contents(agent, "TEST 6")

if __name__ == "__main__":
    test_patient_agent() 