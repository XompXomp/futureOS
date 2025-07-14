#!/usr/bin/env python3
"""
Test script specifically for the web search agent.
Tests web search functionality, query extraction, and memory management.
Shows memory contents after each operation to verify storage.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.web_agent import WebAgent
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
        
        # Check web search namespace memory
        try:
            web_items = agent.store.search(agent.web_namespace, limit=1000)
            print(f"\nWeb Search Memory Items ({agent.web_namespace}): {len(web_items)}")
            for item in web_items:
                print(f"  - Key: {item.key}")
                print(f"    Content: {item.value}")
                print(f"    Created: {item.created_at}")
                print(f"    Updated: {item.updated_at}")
                print()
        except Exception as e:
            print(f"Error accessing web search memory: {str(e)}")
        
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

def test_web_agent():
    """Test the web search agent with various search queries and show memory contents."""
    print("\n" + "="*60)
    print("TESTING WEB SEARCH AGENT - DETAILED ANALYSIS WITH MEMORY INSPECTION")
    print("="*60)
    
    agent = WebAgent()
    
    # Test 1: Basic web search query
    print("\n--- TEST 1: Search for current weather ---")
    state = {
        'user_input': "What's the current weather in New York?",
        'messages': [HumanMessage(content="What's the current weather in New York?")],
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
    
    # Test 2: Search for recent news
    print("\n--- TEST 2: Search for latest technology news ---")
    state = {
        'user_input': "What are the latest technology news today?",
        'messages': [HumanMessage(content="What are the latest technology news today?")],
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
    
    # Test 3: Search for specific information
    print("\n--- TEST 3: Search for Python programming tutorials ---")
    state = {
        'user_input': "Find Python programming tutorials for beginners",
        'messages': [HumanMessage(content="Find Python programming tutorials for beginners")],
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
    
    # Test 4: Search for current events
    print("\n--- TEST 4: Search for current world events ---")
    state = {
        'user_input': "What are the major world events happening right now?",
        'messages': [HumanMessage(content="What are the major world events happening right now?")],
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
    
    # Test 5: Search for specific technical information
    print("\n--- TEST 5: Search for machine learning resources ---")
    state = {
        'user_input': "Find the best machine learning courses and resources",
        'messages': [HumanMessage(content="Find the best machine learning courses and resources")],
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
    
    # Test 6: Test error handling with invalid query
    print("\n--- TEST 6: Test error handling with invalid query ---")
    state = {
        'user_input': "   ",  # Whitespace only
        'messages': [HumanMessage(content="   ")],
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
    
    # Test 7: Test memory retrieval
    print("\n--- TEST 7: Test memory retrieval capabilities ---")
    state = {
        'user_input': "What did we search for earlier about Python?",
        'messages': [HumanMessage(content="What did we search for earlier about Python?")],
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
    
    show_memory_contents(agent, "TEST 7")
    
    print("\n" + "="*60)
    print("WEB SEARCH AGENT TESTING COMPLETED")
    print("="*60)

def test_web_agent_tools():
    """Test the web search tools directly."""
    print("\n" + "="*60)
    print("TESTING WEB SEARCH TOOLS DIRECTLY")
    print("="*60)
    
    try:
        from tools.web_search_tools import search_web, extract_search_query_llm
        
        # Test query extraction
        print("\n--- Testing query extraction ---")
        test_queries = [
            "What's the weather like today?",
            "Find information about artificial intelligence",
            "Search for the latest news about space exploration",
            "What are the best restaurants in San Francisco?",
            "Find tutorials for React.js development"
        ]
        
        for query in test_queries:
            try:
                extracted = extract_search_query_llm(query)
                print(f"Original: '{query}'")
                print(f"Extracted: '{extracted}'")
                print("-" * 40)
            except Exception as e:
                print(f"Error extracting query from '{query}': {str(e)}")
        
        # Test web search tool
        print("\n--- Testing web search tool ---")
        test_search = "Python programming tutorials"
        try:
            result = search_web({
                'user_input': test_search,
                'messages': [HumanMessage(content=test_search)]
            })
            print(f"Search result: {result}")
        except Exception as e:
            print(f"Error in web search: {str(e)}")
            
    except ImportError as e:
        print(f"Could not import web search tools: {str(e)}")
    except Exception as e:
        print(f"Error testing web search tools: {str(e)}")

def test_web_agent_memory_management():
    """Test the web agent's memory management capabilities."""
    print("\n" + "="*60)
    print("TESTING WEB AGENT MEMORY MANAGEMENT")
    print("="*60)
    
    agent = WebAgent()
    
    # Test storing and retrieving information
    print("\n--- Testing memory storage and retrieval ---")
    
    # Store some search results in memory
    test_searches = [
        "machine learning algorithms",
        "data science best practices", 
        "artificial intelligence trends",
        "Python web development frameworks"
    ]
    
    for search_query in test_searches:
        state = {
            'user_input': search_query,
            'messages': [HumanMessage(content=search_query)],
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
            print(f"Stored search for: '{search_query}'")
            if result.get('has_error'):
                print(f"Error: {result.get('error_message')}")
        except Exception as e:
            print(f"Exception storing search '{search_query}': {str(e)}")
    
    # Test memory retrieval
    print("\n--- Testing memory retrieval ---")
    retrieval_queries = [
        "What did we search for about machine learning?",
        "Recall our searches about Python",
        "What information do we have about AI?"
    ]
    
    for query in retrieval_queries:
        state = {
            'user_input': query,
            'messages': [HumanMessage(content=query)],
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
            print(f"Query: '{query}'")
            print(f"Response: {result.get('final_response', 'No response')}")
            if result.get('has_error'):
                print(f"Error: {result.get('error_message')}")
            print("-" * 40)
        except Exception as e:
            print(f"Exception retrieving memory for '{query}': {str(e)}")
    
    show_memory_contents(agent, "MEMORY MANAGEMENT TEST")

if __name__ == "__main__":
    print("Starting Web Agent Tests...")
    
    # Run all tests
    test_web_agent()
    test_web_agent_tools()
    test_web_agent_memory_management()
    
    print("\n🎉 All web agent tests completed!") 