#!/usr/bin/env python3
"""Test script to debug supervisor routing."""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supervisor_workflow import SupervisorWorkflow
from utils.logging_config import logger

def test_routing():
    """Test the supervisor routing with different inputs."""
    workflow = SupervisorWorkflow()
    
    test_cases = [
        ("Hi", "Should route to text_agent"),
        ("What is my name?", "Should route to patient_agent"),
        ("Who is the current US president?", "Should route to web_agent"),
        ("Read patient_profile.json", "Should route to json_agent"),
        ("Read example.txt", "Should route to file_agent"),
        ("What agents do you have?", "Should show all agents")
    ]
    
    print("Testing Supervisor Routing...")
    print("=" * 50)
    
    for user_input, expected in test_cases:
        print(f"\nInput: {user_input}")
        print(f"Expected: {expected}")
        print("-" * 30)
        
        try:
            response = workflow.run(user_input)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print("-" * 30)

if __name__ == "__main__":
    test_routing() 