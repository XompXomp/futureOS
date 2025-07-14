#!/usr/bin/env python3
"""Test script for web agent."""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from config.settings import settings
from tools.web_search_tools import search_web

def test_web_agent():
    """Test the web agent directly."""
    print("Testing web agent...")
    
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
    
    # Create web agent with only core tools (no memory)
    web_agent = create_react_agent(
        model=model,
        tools=[search_web],
        name="web_agent",
        prompt="""You are a web search agent with web search capabilities.

AVAILABLE TOOLS:
- search_web: Search the web for current information

INSTRUCTIONS:
1. ALWAYS provide a conversational response to the user's input
2. When asked for current information, news, or facts → Use search_web tool and provide the results conversationally
3. NEVER output tool call syntax like <|python_tag|>search_web(...) - instead EXECUTE the tool and return the conversational result
4. Be conversational, helpful, and provide meaningful responses
5. If the search doesn't find relevant information, say so conversationally

RESPONSE STRUCTURE:
- For factual questions: Provide a clear, direct answer with supporting details
- For news/information requests: Summarize key findings and mention sources
- For multiple results: Structure your response with bullet points or numbered lists
- Always cite your sources when possible
- Be concise but informative

EXAMPLES:
- User: "Who is the current US president?" → "According to my search, Donald J. Trump is the current US president, serving as the 47th President since January 20, 2025."
- User: "What's the latest news about AI?" → "Based on my search, here are the key AI developments: [list main points with sources]"
- User: "When did superman first appear?" → "Superman first appeared in Action Comics #1 on April 18, 1938, created by Jerry Siegel and Joe Shuster."

IMPORTANT: Always execute tools and provide conversational responses, never output raw tool calls."""
    )
    
    print(f"Created web agent: {web_agent}")
    
    # Test cases
    test_cases = [
        "Who is the current US president?",
        "When did superman first appear?",
        "What is the weather like today?",
        "Who won the last World Cup?",
        "What is the latest news about AI?",
        "What are the best programming languages to learn in 2024?",
        "Tell me about the latest developments in renewable energy",
        "What are the top tourist destinations in Europe?"
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
            result = web_agent.invoke(test_state)
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
    test_web_agent() 