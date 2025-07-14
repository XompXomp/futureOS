#!/usr/bin/env python3
"""Test script for text agent."""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from config.settings import settings
from tools.text_tools import summarize_text, query_database, extract_keywords

def test_text_agent():
    """Test the text agent directly."""
    print("Testing text agent...")
    
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
    
    # Create text agent with only core tools (no memory)
    text_agent = create_react_agent(
        model=model,
        tools=[summarize_text, query_database, extract_keywords],
        name="text_agent",
        prompt="""You are a text processing agent with access to various tools for text analysis.

AVAILABLE TOOLS:
- summarize_text: Summarize long text content
- query_database: Query the database for information  
- extract_keywords: Extract key terms from text

INSTRUCTIONS:
1. Always provide a conversational response to the user's input
2. If the user asks about available agents, list all 5 agents: patient_agent, web_agent, text_agent, file_agent, json_agent
3. For greetings like 'Hello', 'Hi', respond warmly and ask how you can help
4. If the user asks for text analysis, use summarize_text or extract_keywords
5. If the user asks for database queries, use query_database
6. Be conversational, helpful, and provide meaningful responses

EXAMPLES:
- User: 'Hello' → 'Hello! How can I help you today?'
- User: 'What agents do you have?' → 'I have 5 agents: patient_agent, web_agent, text_agent, file_agent, json_agent'
- User: 'How are you?' → 'I'm doing well, thank you for asking! How can I assist you?'"""
    )
    
    print(f"Created text agent: {text_agent}")
    
    # Test cases
    test_cases = [
        "Hello",
        "What agents do you have?",
        "How are you?",
        "Can you summarize this text: The quick brown fox jumps over the lazy dog.",
        "What tools can you use?",
        "Extract keywords from: artificial intelligence machine learning deep learning"
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
            result = text_agent.invoke(test_state)
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
    test_text_agent() 