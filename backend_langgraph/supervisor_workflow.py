#!/usr/bin/env python3
"""LangGraph Supervisor-based multi-agent workflow with proper tool execution."""

import os
import sys
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from typing import Dict, Any, List, Union, Callable
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langchain_community.chat_models import ChatOllama
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_core.runnables import RunnableLambda

from config.settings import settings
from tools.patient_tools import read_patient_profile, update_patient_profile
from tools.web_search_tools import search_web
from tools.text_tools import summarize_text, query_database, extract_keywords
from tools.file_tools import read_file, write_file
from tools.json_tools import read_json_file, write_json_file, list_json_files
from tools.memory_tools import create_memory_tools
from utils.logging_config import logger

def ensure_tool_names(tools):
    for tool in tools:
        if not hasattr(tool, 'name'):
            tool.name = tool.__name__
    return tools

class ToolExecutor:
    """Handles execution of tools when they're output as strings."""
    
    def __init__(self, tools: List):
        self.tools = {tool.name: tool for tool in tools}
        
    def parse_tool_arguments(self, args_str: str) -> Union[str, Dict, List]:
        """Parse tool arguments from string format."""
        args_str = args_str.strip()
        
        # Handle simple string arguments
        if args_str.startswith('"') and args_str.endswith('"'):
            return args_str[1:-1]
        if args_str.startswith("'") and args_str.endswith("'"):
            return args_str[1:-1]
            
        # Handle dictionary arguments
        if args_str.startswith('{') and args_str.endswith('}'):
            try:
                import json
                return json.loads(args_str)
            except:
                return args_str
                
        # Handle list arguments
        if args_str.startswith('[') and args_str.endswith(']'):
            try:
                import json
                return json.loads(args_str)
            except:
                return args_str
                
        # Default to string
        return args_str
        
    def extract_and_execute_tool_calls(self, text: str) -> str:
        """Extract tool calls from text and execute them."""
        # Multiple patterns to catch different tool call formats
        patterns = [
            r'<\|python_tag\|>(\w+)\((.*?)\)',  # <|python_tag|>tool_name("args")
            r'(\w+)\((.*?)\)',  # tool_name("args")
            r'Action:\s*(\w+)\s*Action Input:\s*(.*)',  # ReAct format
        ]
        
        result = text
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            
            if not matches:
                continue
                
            for tool_name, args in matches:
                if tool_name in self.tools:
                    try:
                        # Parse arguments
                        parsed_args = self.parse_tool_arguments(args)
                        
                        # Execute the tool
                        if isinstance(parsed_args, dict):
                            tool_result = self.tools[tool_name](parsed_args)
                        elif isinstance(parsed_args, list):
                            tool_result = self.tools[tool_name](*parsed_args)
                        else:
                            # For string or other types, wrap as state dict
                            tool_result = self.tools[tool_name]({"user_input": parsed_args})
                        
                        # Replace the tool call with the result
                        if pattern.startswith('<\\|python_tag\\|>'):
                            tool_call = f'<|python_tag|>{tool_name}({args})'
                        elif 'Action:' in pattern:
                            tool_call = f'Action: {tool_name}\nAction Input: {args}'
                        else:
                            tool_call = f'{tool_name}({args})'
                            
                        result = result.replace(tool_call, str(tool_result))
                        
                    except Exception as e:
                        logger.error(f"Error executing tool {tool_name}: {str(e)}")
                        
                        # Replace with error message
                        if pattern.startswith('<\\|python_tag\\|>'):
                            tool_call = f'<|python_tag|>{tool_name}({args})'
                        elif 'Action:' in pattern:
                            tool_call = f'Action: {tool_name}\nAction Input: {args}'
                        else:
                            tool_call = f'{tool_name}({args})'
                            
                        result = result.replace(tool_call, f"Error executing {tool_name}: {str(e)}")
        return result

class MessageProcessor:
    """Processes messages to handle tool calls properly."""
    
    def __init__(self, tools: List):
        self.tools = {tool.name: tool for tool in tools}
        
    def process_message(self, message: Union[AIMessage, str]) -> Union[AIMessage, str]:
        """Process a message to execute any embedded tool calls."""
        if isinstance(message, AIMessage):
            content = message.content
        else:
            content = str(message)
        
        # Ensure content is a string for tool call checks
        if not isinstance(content, str):
            content = str(content)
        # Check if the content contains tool calls
        if self.contains_tool_calls(content):
            processed_content = self.execute_tool_calls(content)
            if isinstance(message, AIMessage):
                return AIMessage(content=processed_content, name=message.name)
            else:
                return processed_content
        return message
    
    def contains_tool_calls(self, text: str) -> bool:
        """Check if text contains tool calls."""
        if not isinstance(text, str):
            text = str(text)
        patterns = [
            r'<\|python_tag\|>\w+\(.*?\)',
            r'Action:\s*\w+\s*Action Input:',
            r'\w+\(".*?"\)'
        ]
        
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def execute_tool_calls(self, text: str) -> str:
        """Execute tool calls found in text."""
        if not isinstance(text, str):
            text = str(text)
        executor = ToolExecutor(list(self.tools.values()))
        return executor.extract_and_execute_tool_calls(text)

class EnhancedSupervisorWorkflow:
    def __init__(self, debug_mode: bool = False):
        """Initialize the enhanced supervisor workflow with proper tool execution."""
        self.debug_mode = debug_mode
        # Initialize LLM
        if settings.USE_OLLAMA:
            self.model = ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.3
            )
        elif settings.USE_GROQ:
            self.model = ChatGroq(
                model=settings.LLM_MODEL,
                temperature=0.3
            )
        else:
            raise ValueError("Invalid LLM_PROVIDER. Set LLM_PROVIDER to 'ollama' or 'groq'.")
        
        # Create memory tools for each agent
        self.patient_memory_tools = create_memory_tools("patient_agent")
        self.web_memory_tools = create_memory_tools("web_agent")
        self.text_memory_tools = create_memory_tools("text_agent")
        self.file_memory_tools = create_memory_tools("file_agent")
        self.json_memory_tools = create_memory_tools("json_agent")
        
        # Create tool executors for each agent, ensuring .name attribute
        self.patient_tools = ensure_tool_names([read_patient_profile, update_patient_profile] + self.patient_memory_tools)
        self.web_tools = ensure_tool_names([search_web] + self.web_memory_tools)
        self.text_tools = ensure_tool_names([summarize_text, query_database, extract_keywords] + self.text_memory_tools)
        self.file_tools = ensure_tool_names([read_file, write_file] + self.file_memory_tools)
        self.json_tools = ensure_tool_names([read_json_file, write_json_file, list_json_files] + self.json_memory_tools)
        
        self.patient_executor = ToolExecutor(self.patient_tools)
        self.web_executor = ToolExecutor(self.web_tools)
        self.text_executor = ToolExecutor(self.text_tools)
        self.file_executor = ToolExecutor(self.file_tools)
        self.json_executor = ToolExecutor(self.json_tools)
        
        # Create specialized agents using create_react_agent
        self.patient_agent = create_react_agent(
            model=self.model,
            tools=self.patient_tools,
            name="patient_agent",
            prompt="""You are a patient profile management agent. You MUST use the available tools to provide accurate information.

                    AVAILABLE TOOLS:
                    - read_patient_profile: Read current patient profile from JSON
                    - update_patient_profile: Update patient profile in JSON
                    - Memory tools for storing and retrieving information

                    CRITICAL INSTRUCTIONS:
                    1. ALWAYS use tools when needed - don't make up information
                    2. For patient information queries, ALWAYS call read_patient_profile first
                    3. For updates, ALWAYS call update_patient_profile
                    4. Use tools by calling them directly, not as text strings
                    5. Provide conversational responses after using tools

                    EXAMPLES:
                    - User: "What is my name?" → Call read_patient_profile, then respond conversationally
                    - User: "Update my age to 35" → Call update_patient_profile, then confirm
                    - User: "I am allergic to penicillin" → Call update_patient_profile, then acknowledge

                    Remember: Use tools directly, don't output tool calls as text!"""
        )
        
        self.web_agent = create_react_agent(
            model=self.model,
            tools=self.web_tools,
            name="web_agent",
            prompt="""You are a web search agent. You MUST use the search_web tool for current information.

                AVAILABLE TOOLS:
                - search_web: Search the web for current information
                - Memory tools for storing and retrieving information

                CRITICAL INSTRUCTIONS:
                1. ALWAYS use search_web for current information, news, or facts
                2. Use tools by calling them directly, not as text strings
                3. Never output <|python_tag|> or similar - call tools directly
                4. Provide conversational responses after searching
                5. If search fails, acknowledge and explain

                EXAMPLES:
                - User: "Who is the current US president?" → Call search_web, then respond with results
                - User: "What's the weather like?" → Call search_web, then provide weather info
                - User: "Latest news about AI" → Call search_web, then summarize findings

                Remember: Execute tools directly, don't output tool calls as text!"""
        )
        
        self.text_agent = create_react_agent(
            model=self.model,
            tools=self.text_tools,
            name="text_agent",
            prompt="""You are a text processing agent for general conversation and text analysis.

                AVAILABLE TOOLS:
                - summarize_text: Summarize long text content
                - query_database: Query the database for information  
                - extract_keywords: Extract key terms from text
                - Memory tools for storing and retrieving information

                INSTRUCTIONS:
                1. For greetings, respond warmly without needing tools
                2. For agent listing, respond: "I have 5 agents: patient_agent, web_agent, text_agent, file_agent, json_agent"
                3. For text analysis, use the appropriate tools
                4. Use tools by calling them directly, not as text strings
                5. Be conversational and helpful

                EXAMPLES:
                - User: 'Hello' → 'Hello! How can I help you today?'
                - User: 'What agents do you have?' → List all 5 agents
                - User: 'Summarize this text: [text]' → Use summarize_text tool

                Remember: Call tools directly when needed!"""
        )
        
        self.file_agent = create_react_agent(
            model=self.model,
            tools=self.file_tools,
            name="file_agent",
            prompt="""You are a file management agent. You MUST use the file tools for all file operations.

                AVAILABLE TOOLS:
                - read_file: Read files from the data/docs directory
                - write_file: Write content to files in the data/docs directory
                - Memory tools for storing and retrieving information

                CRITICAL INSTRUCTIONS:
                1. ALWAYS use read_file for reading files
                2. ALWAYS use write_file for writing files
                3. Use tools by calling them directly, not as text strings
                4. Default directory is data/docs
                5. Provide conversational responses after file operations

                EXAMPLES:
                - User: "Read example.txt" → Call read_file, then share contents
                - User: "Write 'Hello World' to test.txt" → Call write_file, then confirm

                Remember: Execute file tools directly!"""
        )
        
        self.json_agent = create_react_agent(
            model=self.model,
            tools=self.json_tools,
            name="json_agent",
            prompt="""You are a JSON file management agent. You MUST use the JSON tools for all JSON operations.

                AVAILABLE TOOLS:
                - read_json_file: Read JSON files from the data/docs directory
                - write_json_file: Write JSON data to files in the data/docs directory
                - list_json_files: List all JSON files in the data/docs directory
                - Memory tools for storing and retrieving information

                CRITICAL INSTRUCTIONS:
                1. ALWAYS use the JSON tools for JSON operations
                2. Use tools by calling them directly, not as text strings
                3. Default directory is data/docs
                4. Provide conversational responses after JSON operations

                EXAMPLES:
                - User: "Read patient_profile.json" → Call read_json_file, then share contents
                - User: "List all JSON files" → Call list_json_files, then list them
                - User: "Write data to config.json" → Call write_json_file, then confirm

                Remember: Execute JSON tools directly!"""
        )
        
        # Create memory tools for memory agent
        self.memory_tools = ensure_tool_names(create_memory_tools("patient_agent"))
        self.memory_agent = create_react_agent(
            model=self.model,
            tools=self.memory_tools,
            name="memory_agent",
            prompt="""
                You are a memory management agent for a healthcare AI system. Your job is to store, retrieve, and manage all types of memory for the patient agent, including semantic, episodic, and procedural memory, as well as prompt rules. You must always use the correct tool for the memory type requested by the user, and confirm the action taken in your response.

                AVAILABLE TOOLS:
                - update_semantic_memory: Store new patient information in semantic memory
                - search_semantic_memory: Retrieve patient information from semantic memory
                - store_episodic_memory: Store successful interactions and their outcomes
                - search_episodic_memory: Retrieve past interactions
                - update_procedural_memory: Update behavior rules and preferences
                - get_procedural_memory: Retrieve behavior rules and preferences
                - optimize_prompt: Optimize prompts using procedural memory
                - get_memory_summary: Get comprehensive memory summary

                INSTRUCTIONS:
                1. Use the correct tool for the memory type requested.
                2. For semantic memory (facts, knowledge, patient info), use update/search_semantic_memory.
                3. For episodic memory (events, interactions, outcomes), use store/search_episodic_memory.
                4. For procedural memory (rules, preferences, prompt rules, and prompt optimization), use update/get_procedural_memory. All prompt optimization is handled as a procedural memory update with category 'prompt_rules'.
                5. For a summary of all memory, use get_memory_summary.
                6. Always confirm the action taken in your response, and be clear about what was stored, retrieved, or updated.
                7. If the user asks for a list, summary, or details, use the appropriate search or summary tool.
                8. If the user asks to update or add information, use the appropriate update/store tool.
                9. If you are unsure, ask for clarification or use get_memory_summary.

                EXAMPLES:
                - User: "I don't like rude way of talking."
                → Use update_procedural_memory with rule_type "communication_style", rule_data {"politeness": "prefer polite, not rude"}, and confirm update.
                - User: "Make it more technical."
                → Use update_procedural_memory with rule_type "prompt_rules", rule_data {"technical_prompt": "<user's prompt or context>"}. The system will optimize the prompt with the LLM and store it in procedural memory.
                - User: "I had a great appointment today."
                → Use store_episodic_memory with interaction_type "appointment", content "great appointment today", and confirm storage.
                - User: "Allergies: penicillin."
                → Use update_semantic_memory with content "penicillin", category "allergy", and confirm update.
                - User: "I prefer morning appointments."
                → Use update_procedural_memory with rule_type "appointment_preferences", rule_data {"time": "morning"}, and confirm update.
                - User: "Show my last two visits."
                → Use search_episodic_memory with limit 2 and summarize the results.
                - User: "Summarize my memory."
                → Use get_memory_summary and provide a summary.
                - User: "What are my prompt rules?"
                → Use get_procedural_memory with rule_type "prompt_rules" and list the rules.

                Remember: Always use the correct tool, confirm the action, and be clear and helpful in your response.
                """
        )
        
        # Create message processors for each agent
        self.patient_processor = MessageProcessor(self.patient_tools)
        self.web_processor = MessageProcessor(self.web_tools)
        self.text_processor = MessageProcessor(self.text_tools)
        self.file_processor = MessageProcessor(self.file_tools)
        self.json_processor = MessageProcessor(self.json_tools)
        
        # Map agents to their processors
        self.agent_processors = {
            "patient_agent": self.patient_processor,
            "web_agent": self.web_processor,
            "text_agent": self.text_processor,
            "file_agent": self.file_processor,
            "json_agent": self.json_processor
        }
        
        # Create supervisor workflow
        self.workflow = create_supervisor(
            [self.patient_agent, self.web_agent, self.text_agent, self.file_agent, self.json_agent, self.memory_agent],
            model=self.model,
            prompt="""
You are a supervisor for a team of specialized agents in a healthcare AI system.

AVAILABLE AGENTS:
- patient_agent: Handles patient profile queries, updates, and medical information
- web_agent: Handles web searches and online information gathering
- text_agent: Handles text processing, summarization, general conversation, and listing all available agents
- file_agent: Handles file operations like reading, writing, and managing documents
- json_agent: Handles JSON file operations (read, write, list JSON files)
- memory_agent: Handles all memory management tasks (semantic, episodic, procedural, and prompt rules) for the patient agent

ROUTING INSTRUCTIONS:
- Output ONLY the agent name, exactly as: patient_agent, web_agent, text_agent, file_agent, json_agent, or memory_agent
- Do not output anything else or explain your choice
- For greetings, general conversation, or agent listing → text_agent
- For patient info, medical data, or personal details → patient_agent
- For file operations → file_agent
- For JSON operations → json_agent
- For memory management (semantic, episodic, procedural, or prompt rules) → memory_agent
- **For ANY fact-based, current event, general knowledge, or up-to-date information question (e.g., 'Who is...', 'What is...', 'When did...', 'How many...', 'What year...', 'What is the population of...', 'When did the Olympics start?', 'Who is the CEO of...', 'What is the latest news about...', 'What is the weather like?', etc.), or anything that may require information not found in memory, ALWAYS route to → web_agent**

EXAMPLES:
- User: "Who is the current US president?" → web_agent
- User: "What is the population of India?" → web_agent
- User: "When did the Olympics start?" → web_agent
- User: "Latest news about AI" → web_agent
- User: "What's the weather like?" → web_agent
- User: "What is my name?" → patient_agent
- User: "Summarize this text: ..." → text_agent
- User: "Read example.txt" → file_agent
- User: "List all JSON files" → json_agent
- User: "Update my age to 35" → patient_agent

Remember: Be strict and explicit in your routing. If in doubt, prefer web_agent for fact-based or current event queries.
"""
        )
        
        # Setup session memory
        self.checkpointer = InMemorySaver()
        self.store = InMemoryStore()
        
        # Compile the workflow
        self.app = self.workflow.compile(
            checkpointer=self.checkpointer,
            store=self.store
        )
        
        logger.info("Enhanced supervisor workflow initialized successfully")

    def process_workflow_messages(self, messages: List) -> List:
        """Process only the latest user/assistant message pair for tool calls, with debug logging."""
        processed_messages = []
        
        # Find the latest user message and its following assistant message
        latest_user_idx = None
        for i in range(len(messages) - 1, -1, -1):
            msg = messages[i]
            if (isinstance(msg, dict) and msg.get("role") == "user") or (hasattr(msg, "role") and getattr(msg, "role", None) == "user"):
                latest_user_idx = i
                break
        
        # Only process from the latest user message onwards
        if latest_user_idx is not None:
            to_process = messages[latest_user_idx:]
        else:
            to_process = messages[-2:] if len(messages) >= 2 else messages
        
        for idx, message in enumerate(messages):
            # Only process tool calls for the latest user/assistant pair
            if message in to_process:
                # Only process tool calls if not already processed
                if isinstance(message, dict):
                    if message.get('tool_processed', False):
                        processed_messages.append(message)
                        print(f"[DEBUG] Skipping already processed message: {message}")
                        continue
                    if message.get("role") == "assistant" and message.get("content"):
                        # Try to determine which agent sent this message
                        agent_name = self.determine_agent_from_message(message)
                        if agent_name in self.agent_processors:
                            processor = self.agent_processors[agent_name]
                            # Only call process_message if message is AIMessage or str
                            # For dicts, skip processing to avoid type errors
                            # Mark as processed to avoid re-processing
                            message['tool_processed'] = True  # Mark as processed
                            print(f"[DEBUG] Marked dict message as processed for agent: {agent_name}")
                    processed_messages.append(message)
            else:
                processed_messages.append(message)
        return processed_messages
    
    def determine_agent_from_message(self, message: dict) -> str:
        """Determine which agent sent a message."""
        # Simple heuristic - you might need to enhance this
        content = message.get("content", "")
        if "patient" in content.lower():
            return "patient_agent"
        elif "search" in content.lower() or "web" in content.lower():
            return "web_agent"
        elif "file" in content.lower():
            return "file_agent"
        elif "json" in content.lower():
            return "json_agent"
        else:
            return "text_agent"

    def post_process_agent_response(self, response: str, agent_name: str) -> str:
        """Post-process agent response to execute any tool calls."""
        if agent_name in self.agent_processors:
            processor = self.agent_processors[agent_name]
            return processor.execute_tool_calls(response)
        return response

    def llm_memory_categorizer(self, user_input: str) -> list:
        """Use the LLM to decide if/what to store in memory, and how to categorize it."""
        from langchain_core.prompts import ChatPromptTemplate
        import json
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
You are a memory categorization assistant. Given a user input, decide if any information should be stored in memory. 
- ONLY store information if it is a fact, preference, or something about the user or patient (e.g., 'I am allergic to penicillin', 'My favorite color is blue', 'I prefer polite conversation').
- DO NOT store questions, requests for information, or queries (e.g., 'Who is the current US president?', 'What is the weather?', 'When is the next holiday?').
- For each relevant memory type (semantic, episodic, procedural), output a JSON object with the following fields as appropriate:
  - type: one of 'semantic', 'episodic', 'procedural'
  - content: what to store (string or dict)
  - category: (for semantic/procedural, e.g. 'allergy', 'preference', 'prompt_rules')
  - interaction_type, outcome, reasoning_context: (for episodic)
- If the user input is a prompt or prompt rule update, treat it as a procedural memory update with category 'prompt_rules'.
- The user may not use explicit commands; they may express preferences, dislikes, or suggestions in a conversational way (e.g., 'I don't like rude way of talking', 'make it more technical'). Infer the correct memory update from such statements.
- If nothing should be stored, return an empty list.
- Output a JSON list of objects, no explanation or extra text.
"""),
            ("human", "User input: {user_input}\n\nMemory update JSON:")
        ])
        chain = prompt | self.model
        summary = chain.invoke({"user_input": user_input})
        # Try to parse the output as JSON list
        try:
            # If the LLM output is wrapped in a code block, strip it
            text = summary.content if hasattr(summary, 'content') else str(summary)
            text = str(text).strip()
            if text.startswith('```'):
                text = text.strip('`').strip()
                if text.startswith('json'):
                    text = text[4:].strip()
            updates = json.loads(text)
            if isinstance(updates, dict):
                updates = [updates]
            if not isinstance(updates, list):
                return []
            # --- PROGRAMMATIC FILTER: Remove updates that are just the user query or a question ---
            filtered_updates = []
            for update in updates:
                content = update.get('content', '').strip().lower()
                # Skip if content is empty
                if not content:
                    continue
                # Skip if content is just the user query (ignoring case and punctuation)
                import re
                def normalize(s):
                    return re.sub(r'[^a-z0-9]', '', s.lower())
                if normalize(content) == normalize(user_input):
                    continue
                # Skip if content is a question (ends with '?', starts with 'who', 'what', 'when', 'where', 'how', etc.)
                question_words = ['who', 'what', 'when', 'where', 'how', 'why', 'is', 'are', 'do', 'does', 'can', 'could', 'would', 'should', 'will']
                if content.endswith('?') or any(content.startswith(qw + ' ') for qw in question_words):
                    continue
                filtered_updates.append(update)
            return filtered_updates
            # --- END FILTER ---
        except Exception as e:
            logger.error(f"Error parsing LLM memory categorizer output: {e}, raw: {summary}")
            return []

    def update_memory_from_categorizer(self, memory_updates: list):
        """Call the appropriate memory tool for each update object."""
        results = []
        for update in memory_updates:
            mtype = update.get('type')
            if mtype == 'semantic':
                tool = next((t for t in self.memory_tools if t.name == 'update_semantic_memory'), None)
                if tool:
                    result = tool({
                        'content': update.get('content', ''),
                        'category': update.get('category', 'general'),
                        'metadata': update.get('metadata', {})
                    })
                    results.append(result)
            elif mtype == 'episodic':
                tool = next((t for t in self.memory_tools if t.name == 'store_episodic_memory'), None)
                if tool:
                    result = tool({
                        'interaction_type': update.get('interaction_type', ''),
                        'content': update.get('content', ''),
                        'reasoning_context': update.get('reasoning_context', ''),
                        'outcome': update.get('outcome', ''),
                        'metadata': update.get('metadata', {})
                    })
                    results.append(result)
            elif mtype == 'procedural':
                tool = next((t for t in self.memory_tools if t.name == 'update_procedural_memory'), None)
                if tool:
                    result = tool({
                        'rule_type': update.get('category', ''),
                        'rule_data': update.get('content', {})
                    })
                    results.append(result)
        return results

    def llm_postprocess_response(self, tool_output, user_input):
        """Use the LLM to generate a conversational answer from the tool output and user input."""
        try:
            from langchain_core.prompts import ChatPromptTemplate
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant. Given the following tool result and the user's question, answer as helpfully and conversationally as possible. If the tool result contains web search results, use only the most recent and explicit information from the top 5 results to answer fact-based questions (such as 'Who is the current US president?'). If there is any ambiguity or the answer is not explicit, say 'I cannot determine with certainty.' Always prefer the most recent, date-stamped, and explicit answer."),
                ("human", "Tool result: {tool_output}\n\nUser question: {user_input}\n\nAnswer:")
            ])
            chain = prompt | self.model
            summary = chain.invoke({"tool_output": str(tool_output), "user_input": user_input})
            if hasattr(summary, 'content'):
                return summary.content
            return str(summary)
        except Exception as e:
            logger.error(f"Error in LLM post-processing: {str(e)}")
            return str(tool_output)

    def run(self, user_input: str) -> str:
        """Run the supervisor workflow with user input."""
        try:
            # --- NEW: Semantic memory pre-check step with perfect match threshold ---
            search_tool = next((t for t in self.memory_tools if t.name == 'search_semantic_memory'), None)
            perfect_match_threshold = 0.95
            perfect_match = None
            if search_tool:
                search_result = search_tool({
                    'query': user_input,
                    'limit': 3
                })
                results = search_result.get('results', [])
                # Check for a perfect match (assume 'similarity' key is present, else skip)
                for r in results:
                    if r.get('similarity', 0) >= perfect_match_threshold:
                        perfect_match = r
                        break
                if perfect_match:
                    response = f"I found an exact match in my memory:\n- {perfect_match.get('content', '')}"
                    return str(self.llm_postprocess_response(response, user_input))
                # Otherwise, proceed as normal
                if not results:
                    preface = "I didn't know this, I will add it to my memory."
                else:
                    preface = None
            else:
                preface = None
            # --- END NEW ---

            # LLM-powered memory categorization and update step
            memory_updates = self.llm_memory_categorizer(user_input)
            logger.info(f"[DEBUG] Memory categorizer updates: {memory_updates}")
            if memory_updates:
                memory_results = self.update_memory_from_categorizer(memory_updates)
                logger.info(f"[DEBUG] Memory update results: {memory_results}")
            # Create initial state
            initial_state = {
                "messages": [
                    {"role": "user", "content": user_input}
                ]
            }
            
            # Create config
            config = {
                "configurable": {
                    "thread_id": "default_thread",
                    "checkpoint_ns": "supervisor_workflow"
                }
            }
            
            # Run the workflow
            result = self.app.invoke(initial_state, config=config)
            
            if result is None:
                logger.error("Supervisor workflow returned None as result.")
                return "I apologize, but I encountered an internal error (no result)."
            
            # Extract messages and process them
            messages = result.get("messages", [])
            
            # Process all messages to execute any tool calls
            processed_messages = self.process_workflow_messages(messages)
            
            final_response = None
            last_agent = None
            
            # Prefer final_response if present
            if result.get("final_response"):
                logger.info(f"[DEBUG] Supervisor: Using result['final_response']: {result['final_response']}")
                final_response = result["final_response"]
            else:
                # Find the final response from processed messages
                for message in reversed(processed_messages):
                    if isinstance(message, dict):
                        if (message.get("role") == "assistant" and message.get("content")):
                            content = message["content"].strip()
                            if not (content.endswith("_agent") and content.replace('_agent', '').isidentifier()):
                                final_response = content
                                break
                    elif hasattr(message, 'content') and hasattr(message, 'name'):
                        content = str(message.content).strip()
                        if (not content.endswith("_agent") and 
                            not content.startswith("Transferring") and
                            not content.startswith("Successfully") and
                            content):
                            final_response = content
                            last_agent = message.name
                            break
                # Additional post-processing if needed
                if final_response and last_agent:
                    final_response = self.post_process_agent_response(final_response, last_agent)
                if not final_response:
                    logger.info("[DEBUG] Supervisor: No final_response found in messages, using fallback.")
                    final_response = result.get("final_response", "No response generated")
            # LLM post-processing for user-friendly answer
            logger.info(f"[DEBUG] Supervisor: Pre-LLM postprocess final_response: {final_response}")
            conversational_response = self.llm_postprocess_response(final_response, user_input)
            logger.info(f"[DEBUG] Supervisor: Post-LLM postprocess conversational_response: {conversational_response}")
            logger.info(f"[EXPLICIT DEBUG] Supervisor about to return: type={type(conversational_response)}, value={conversational_response}")
            if 'preface' in locals() and preface:
                return f"{preface}\n{str(conversational_response)}"
            return str(conversational_response)
        except Exception as e:
            logger.error(f"Error running supervisor workflow: {str(e)}")
            return f"I apologize, but I encountered an error: {str(e)}"

    def chat(self, debug: bool = False):
        """Start interactive chat session."""
        self.debug_mode = debug
        print("Enhanced LangGraph Supervisor AI Agent is ready! Type 'quit' to exit.")
        if debug:
            print("DEBUG MODE: Detailed logging enabled")
        print("You can:")
        print("- Ask questions about your patient profile")
        print("- Update your patient information")
        print("- Read/write files")
        print("- Search the web")
        print("- Summarize text")
        print("- Query the database")
        print()
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("Goodbye!")
                    break
                
                if user_input.lower() == 'debug':
                    self.debug_mode = not self.debug_mode
                    print(f"Debug mode: {'ON' if self.debug_mode else 'OFF'}")
                    continue
                
                if not user_input:
                    continue
                
                response = self.run(user_input)
                print(f"Agent: {response}")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
                if debug:
                    import traceback
                    print(f"Full traceback:\n{traceback.format_exc()}")

def main():
    """Main function to run the enhanced supervisor workflow."""
    try:
        # Create necessary directories
        os.makedirs("data", exist_ok=True)
        os.makedirs("data/docs", exist_ok=True)
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Check for debug flag
        debug_mode = "--debug" in sys.argv or "-d" in sys.argv
        
        # Initialize and run enhanced supervisor workflow
        workflow = EnhancedSupervisorWorkflow(debug_mode=debug_mode)
        workflow.chat(debug=debug_mode)
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        print(f"Failed to start enhanced supervisor workflow: {str(e)}")
        if "--debug" in sys.argv or "-d" in sys.argv:
            import traceback
            print(f"Full traceback:\n{traceback.format_exc()}")

if __name__ == "__main__":
    main() 