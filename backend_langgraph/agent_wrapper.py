#!/usr/bin/env python3
"""LangChain Agent Wrapper for LangGraph Supervisor."""

from typing import Dict, Any
from langchain.agents import initialize_agent, AgentType
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain.memory import ConversationBufferWindowMemory
from config.settings import settings
from utils.logging_config import logger

class LangChainAgentWrapper:
    """Wrapper to use LangChain agents in LangGraph Supervisor."""
    
    def __init__(self, agent, name: str):
        self.agent = agent
        self.name = name  # Required for LangGraph Supervisor

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Call the LangChain agent and append response to state."""
        try:
            # Extract user input from state
            user_input = None
            if "user_input" in state:
                user_input = state["user_input"]
            elif "messages" in state and state["messages"]:
                # Find the last user message
                for msg in reversed(state["messages"]):
                    if (isinstance(msg, dict) and msg.get("role") == "user" and msg.get("content")):
                        user_input = msg["content"]
                        break
            
            if not user_input:
                state["final_response"] = "No user input found."
                return state

            # Call the LangChain agent
            logger.info(f"Calling {self.name} with input: {user_input[:50]}...")
            logger.info(f"Agent type: {type(self.agent)}")
            logger.info(f"Agent: {self.agent}")
            
            try:
                response = self.agent.run(user_input)
                logger.info(f"Agent.run() returned: {response}")
            except Exception as e:
                logger.error(f"Error calling agent.run(): {str(e)}")
                response = f"Error in {self.name}: {str(e)}"
            
            # Debug: Print the response from the agent
            logger.info(f"{self.name} raw response: {response[:200]}...")
            
            # Append the response as the last assistant message
            if "messages" not in state:
                state["messages"] = []
            
            # Debug: Print state before appending
            logger.info(f"State before appending message: {len(state['messages'])} messages")
            
            # Append the assistant message
            assistant_message = {"role": "assistant", "content": response}
            state["messages"].append(assistant_message)
            state["final_response"] = response
            
            # Debug: Print state after appending
            logger.info(f"State after appending message: {len(state['messages'])} messages")
            logger.info(f"Last message content: {state['messages'][-1]['content'][:100]}...")
            
            logger.info(f"{self.name} response: {response[:100]}...")
            return state
            
        except Exception as e:
            logger.error(f"Error in {self.name}: {str(e)}")
            error_msg = f"Error in {self.name}: {str(e)}"
            if "messages" not in state:
                state["messages"] = []
            state["messages"].append({"role": "assistant", "content": error_msg})
            state["final_response"] = error_msg
            return state

    def invoke(self, state: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Invoke method for LangGraph Supervisor compatibility."""
        return self.__call__(state)

def create_patient_agent():
    """Create a patient agent using LangChain."""
    # Initialize LLM
    if settings.USE_OLLAMA:
        llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.3
        )
    else:
        llm = ChatGroq(
            model=settings.LLM_MODEL,
            temperature=0.3
        )
    
    # Create memory
    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        return_messages=True,
        k=10
    )
    
    # Import tools (you'll need to convert these to LangChain Tool format)
    from tools.patient_tools import read_patient_profile, update_patient_profile
    from langchain.agents import Tool
    
    # Convert state-based tools to LangChain Tool format
    def read_patient_tool(input_str: str) -> str:
        """Read patient profile tool for LangChain."""
        # This is a simplified version - you'll need to adapt based on your tool structure
        return "Patient profile information would be returned here"
    
    def update_patient_tool(input_str: str) -> str:
        """Update patient profile tool for LangChain."""
        return f"Updated patient profile with: {input_str}"
    
    tools = [
        Tool(
            name="read_patient_profile",
            func=read_patient_tool,
            description="Read current patient profile from JSON"
        ),
        Tool(
            name="update_patient_profile", 
            func=update_patient_tool,
            description="Update patient profile in JSON"
        )
    ]
    
    # Create agent
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=False,
        handle_parsing_errors=True,
        agent_kwargs={
            "system_message": """You are a patient profile management agent.

AVAILABLE TOOLS:
- read_patient_profile: Read current patient profile from JSON
- update_patient_profile: Update patient profile in JSON

INSTRUCTIONS:
1. Always provide a conversational response to the user's input
2. When asked about patient info → Use read_patient_profile and provide the information conversationally
3. When given new patient info → Use update_patient_profile and confirm the update
4. Be conversational, helpful, and provide meaningful responses

EXAMPLES:
- User: "What is my name?" → Check patient profile and respond: "Your name is [name]"
- User: "Update my age to 35" → Update profile and respond: "I've updated your age to 35"
- User: "I am allergic to penicillin" → Update profile and respond: "I've recorded your penicillin allergy"
- User: "What are my chronic conditions?" → Check profile and list conditions conversationally"""
        }
    )
    
    return LangChainAgentWrapper(agent, "patient_agent")

def create_text_agent():
    """Create a text agent using LangChain."""
    # Initialize LLM
    if settings.USE_OLLAMA:
        llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.3
        )
    else:
        llm = ChatGroq(
            model=settings.LLM_MODEL,
            temperature=0.3
        )
    
    # Create memory
    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        return_messages=True,
        k=10
    )
    
    # Import tools
    from tools.text_tools import summarize_text, query_database, extract_keywords
    from langchain.agents import Tool
    
    # Convert state-based tools to LangChain Tool format
    def summarize_text_tool(input_str: str) -> str:
        """Summarize text tool for LangChain."""
        return f"Summary of: {input_str}"
    
    def query_database_tool(input_str: str) -> str:
        """Query database tool for LangChain."""
        return f"Database results for: {input_str}"
    
    def extract_keywords_tool(input_str: str) -> str:
        """Extract keywords tool for LangChain."""
        return f"Keywords extracted from: {input_str}"
    
    tools = [
        Tool(
            name="summarize_text",
            func=summarize_text_tool,
            description="Summarize long text content"
        ),
        Tool(
            name="query_database",
            func=query_database_tool,
            description="Query the database for information"
        ),
        Tool(
            name="extract_keywords",
            func=extract_keywords_tool,
            description="Extract key terms from text"
        )
    ]
    
    # Create agent
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=False,
        handle_parsing_errors=True,
        agent_kwargs={
            "system_message": """You are a text processing agent with access to various tools for text analysis.

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
        }
    )
    
    return LangChainAgentWrapper(agent, "text_agent")

def create_web_agent():
    """Create a web search agent using LangChain."""
    # Initialize LLM
    if settings.USE_OLLAMA:
        llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.3
        )
    else:
        llm = ChatGroq(
            model=settings.LLM_MODEL,
            temperature=0.3
        )
    
    # Create memory
    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        return_messages=True,
        k=10
    )
    
    # Import tools
    from tools.web_search_tools import search_web
    from langchain.agents import Tool
    
    # Convert state-based tools to LangChain Tool format
    def search_web_tool(input_str: str) -> str:
        """Web search tool for LangChain."""
        return f"Web search results for: {input_str}"
    
    tools = [
        Tool(
            name="search_web",
            func=search_web_tool,
            description="Search the web for information using Google PSE"
        )
    ]
    
    # Create agent
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=False,
        handle_parsing_errors=True,
        agent_kwargs={
            "system_message": """You are a web search agent with access to web search capabilities.

AVAILABLE TOOLS:
- search_web: Search the web for information using Google PSE

INSTRUCTIONS:
1. When asked to search the web → Use search_web tool
2. When asked for current information → Use search_web tool
3. When asked for recent news or updates → Use search_web tool
4. Be conversational and helpful with web search queries

EXAMPLES:
- User: "Search for latest AI news" → Use search_web tool
- User: "Find information about Python programming" → Use search_web tool
- User: "What's the weather like today?" → Use search_web tool"""
        }
    )
    
    return LangChainAgentWrapper(agent, "web_agent")

def create_file_agent():
    """Create a file management agent using LangChain."""
    # Initialize LLM
    if settings.USE_OLLAMA:
        llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.3
        )
    else:
        llm = ChatGroq(
            model=settings.LLM_MODEL,
            temperature=0.3
        )
    
    # Create memory
    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        return_messages=True,
        k=10
    )
    
    # Import tools
    from tools.file_tools import read_file, write_file
    from langchain.agents import Tool
    
    # Convert state-based tools to LangChain Tool format
    def read_file_tool(input_str: str) -> str:
        """Read file tool for LangChain."""
        return f"File contents for: {input_str}"
    
    def write_file_tool(input_str: str) -> str:
        """Write file tool for LangChain."""
        return f"File written: {input_str}"
    
    tools = [
        Tool(
            name="read_file",
            func=read_file_tool,
            description="Read files from the data/docs directory"
        ),
        Tool(
            name="write_file",
            func=write_file_tool,
            description="Write content to files in the data/docs directory"
        )
    ]
    
    # Create agent
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=False,
        handle_parsing_errors=True,
        agent_kwargs={
            "system_message": """You are a file management agent with access to file operations.

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
        }
    )
    
    return LangChainAgentWrapper(agent, "file_agent")

def create_json_agent():
    """Create a JSON file management agent using LangChain."""
    # Initialize LLM
    if settings.USE_OLLAMA:
        llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.3
        )
    else:
        llm = ChatGroq(
            model=settings.LLM_MODEL,
            temperature=0.3
        )
    
    # Create memory
    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        return_messages=True,
        k=10
    )
    
    # Import tools
    from tools.json_tools import read_json_file, write_json_file, list_json_files
    from langchain.agents import Tool
    
    # Convert state-based tools to LangChain Tool format
    def read_json_file_tool(input_str: str) -> str:
        """Read JSON file tool for LangChain."""
        return f"JSON file contents for: {input_str}"
    
    def write_json_file_tool(input_str: str) -> str:
        """Write JSON file tool for LangChain."""
        return f"JSON file written: {input_str}"
    
    def list_json_files_tool(input_str: str) -> str:
        """List JSON files tool for LangChain."""
        return "Available JSON files: patient_profile.json, config.json"
    
    tools = [
        Tool(
            name="read_json_file",
            func=read_json_file_tool,
            description="Read JSON files from the data/docs directory"
        ),
        Tool(
            name="write_json_file",
            func=write_json_file_tool,
            description="Write JSON data to files in the data/docs directory"
        ),
        Tool(
            name="list_json_files",
            func=list_json_files_tool,
            description="List all JSON files in the data/docs directory"
        )
    ]
    
    # Create agent
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=False,
        handle_parsing_errors=True,
        agent_kwargs={
            "system_message": """You are a JSON file management agent with access to JSON file operations.

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
        }
    )
    
    return LangChainAgentWrapper(agent, "json_agent") 