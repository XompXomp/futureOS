#!/usr/bin/env python3
"""LangGraph Supervisor-based multi-agent workflow with proper tool execution."""

import os
import sys
import re
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from typing import Dict, Any, List, Union, Callable, Optional
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
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate

from config.settings import settings
from tools.patient_tools import read_patient_profile, update_patient_profile
from tools.web_search_tools import search_web
from tools.text_tools import summarize_text, query_database, extract_keywords
from tools.json_tools import read_json_file, write_json_file, list_json_files
from tools.memory_tools import create_memory_tools
from utils.logging_config import logger

def ensure_tool_names(tools):
    for tool in tools:
        if not hasattr(tool, 'name'):
            tool.name = tool.__name__
    return tools

class EnhancedSupervisorWorkflow:
    def __init__(self, debug_mode: bool = False):
        """Initialize the enhanced supervisor workflow with proper tool execution."""
        self.debug_mode = debug_mode
        # Initialize LLM
        if settings.USE_OLLAMA:
            self.reasoning_model = ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.3
            )
        elif settings.USE_GROQ:
            self.reasoning_model = ChatGroq(
                model=settings.LLM_MODEL,
                temperature=0.3
            )
        else:
            raise ValueError("Invalid LLM_PROVIDER. Set LLM_PROVIDER to 'ollama' or 'groq'.")
        
        # Instantiate memory_tools as a module (not as agent tools)
        self.memory_tools = {tool.name: tool for tool in ensure_tool_names(create_memory_tools("patient_agent"))}
        
        # Create tool executors for each agent, ensuring .name attribute
        self.patient_tools = ensure_tool_names([read_patient_profile, update_patient_profile])
        self.web_tools = ensure_tool_names([search_web])# + self.web_memory_tools)
        self.text_tools = ensure_tool_names([summarize_text, query_database, extract_keywords])# + self.text_memory_tools)
        self.json_tools = ensure_tool_names([read_json_file, write_json_file, list_json_files])# + self.json_memory_tools)
        
        # Create specialized agents using create_react_agent
        self.patient_agent = create_react_agent(
            model=self.reasoning_model,
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
            model=self.reasoning_model,
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
            model=self.reasoning_model,
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
        
        self.json_agent = create_react_agent(
            model=self.reasoning_model,
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
        
        # Remove memory_agent from members
        members = ["patient_agent", "web_agent", "text_agent", "json_agent"]
        # --- Semantic Memory Pre-Check Node ---
        def semantic_memory_precheck_node(state: Dict[str, Any]):
            search_tool = self.memory_tools.get('search_semantic_memory_tool')
            update_tool = self.memory_tools.get('update_semantic_memory_tool')
            if not search_tool:
                return state, "supervisor"
            search_result = search_tool({
                'query': state['user_input'],
                'limit': 3,
                'memory': state.get('memory', {})
            })
            results = search_result.get('results', [])
            if results:
                all_contents = "\n- ".join(r.get('content', '') for r in results)
                memory_response = f"I found these in your memory:\n- {all_contents}"
                prompt = ChatPromptTemplate.from_template(
                    "Is the following memory relevant to the user's question? Respond 'true' or 'false'.\nUser: {user_input}\nMemory: {all_contents}\nAnswer:"
                )
                chain = prompt | self.reasoning_model
                relevance_result = chain.invoke({"user_input": state['user_input'], "all_contents": all_contents})
                relevance = str(relevance_result.content).strip().lower()
                if 'true' in relevance:
                    state['messages'].append(HumanMessage(content=memory_response))
                    return state, END
            # If not relevant, treat as a new fact and update semantic memory
            if update_tool:
                result = update_tool({
                    'content': state['user_input'],
                    'category': 'general',
                    'memory': state.get('memory', {})
                })
                state['memory'] = result.get('memory', state.get('memory', {}))
            return state, "supervisor"
        # --- Supervisor Router Node ---
        supervisor_prompt = """
You are a supervisor for a team of specialized agents in a healthcare AI system.

AVAILABLE AGENTS:
- patient_agent: Handles patient profile queries, updates, and medical information
- web_agent: Handles web searches and online information gathering
- text_agent: Handles text processing, summarization, general conversation, and listing all available agents
- json_agent: Handles JSON file operations (read, write, list JSON files)

ROUTING INSTRUCTIONS:
- Output ONLY the agent name, exactly as: patient_agent, web_agent, text_agent, or json_agent
- Do not output anything else or explain your choice
- For greetings, general conversation, or agent listing → text_agent
- For patient info, medical data, or personal details → patient_agent
- For JSON operations → json_agent
- For any fact-based, current event, general knowledge, or up-to-date information question (e.g., 'Who is...', 'What is...', 'When did...', 'How many...', 'What year...', 'What is the population of...', 'When did the Olympics start?', 'Who is the CEO of...', 'What is the latest news about...', 'What is the weather like?', etc.), or anything that may require information not found in memory, ALWAYS route to → web_agent

EXAMPLES:
- User: "Who is the current US president?" → web_agent
- User: "What is the population of India?" → web_agent
- User: "When did the Olympics start?" → web_agent
- User: "Latest news about AI" → web_agent
- User: "What's the weather like?" → web_agent
- User: "What is my name?" → patient_agent
- User: "Summarize this text: ..." → text_agent
- User: "List all JSON files" → json_agent
- User: "Update my age to 35" → patient_agent

Remember: Be strict and explicit in your routing. If in doubt, prefer web_agent for fact-based or current event queries.
"""
        def supervisor_router(state: Dict[str, Any]):
            prompt = ChatPromptTemplate.from_messages([
                ("system", supervisor_prompt),
                ("human", "User input: {user_input}")
            ])
            chain = prompt | self.reasoning_model
            result = chain.invoke({"user_input": state['user_input']})
            agent_name = str(result.content).strip()
            if agent_name in members:
                return agent_name
            return "text_agent"
        # --- Build the custom graph ---
        class AgentState(dict):
            pass
        graph_builder = StateGraph(AgentState)
        graph_builder.add_node("semantic_precheck", semantic_memory_precheck_node)
        graph_builder.add_node("supervisor", supervisor_router)
        graph_builder.add_node("patient_agent", self.patient_agent)
        graph_builder.add_node("web_agent", self.web_agent)
        graph_builder.add_node("text_agent", self.text_agent)
        graph_builder.add_node("json_agent", self.json_agent)
        graph_builder.set_entry_point("semantic_precheck")
        graph_builder.add_edge("semantic_precheck", "supervisor")
        for member in members:
            graph_builder.add_edge(member, "supervisor")
        graph_builder.add_conditional_edges(
            "supervisor",
            supervisor_router,
            {member: member for member in members}
        )
        self.app = graph_builder.compile(checkpointer=InMemorySaver())
        logger.info("Enhanced supervisor workflow with semantic pre-check and LLM supervisor routing initialized successfully")
        
        # Setup session memory
        self.checkpointer = InMemorySaver()
        self.store = InMemoryStore()
        
        # Compile the workflow
        # self.app = self.workflow.compile(
        #     checkpointer=self.checkpointer,
        #     store=self.store
        # )
        
        logger.info("Enhanced supervisor workflow initialized successfully")

    def llm_memory_categorizer(self, user_input: str, memory: dict) -> list:
        """Use the LLM to decide if/what to store in memory, and how to categorize it, excluding patient profile fields."""
        from langchain_core.prompts import ChatPromptTemplate
        import json
        # Load patient profile fields
        try:
            with open(settings.PATIENT_PROFILE_PATH, 'r') as f:
                profile = json.load(f)
            def flatten_keys(d, prefix=""):
                keys = []
                for k, v in d.items():
                    full_key = f"{prefix}.{k}" if prefix else k
                    keys.append(full_key)
                    if isinstance(v, dict):
                        keys.extend(flatten_keys(v, full_key))
                return keys
            profile_keys = flatten_keys(profile)
        except Exception as e:
            profile_keys = []
        profile_keys_str = ', '.join(profile_keys)
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""
            You are a memory categorization assistant. Given a user input, decide if any information should be stored in memory.
            - ONLY store information if it is a fact, preference, or something about the user or patient (e.g., 'I am allergic to penicillin', 'My favorite color is blue', 'I prefer polite conversation').
            - DO NOT store questions, requests for information, or queries (e.g., 'Who is the current US president?', 'What is the weather?', 'When is the next holiday?').
            - If the user input is related to any of the following patient profile fields, DO NOT add it to memory (patient info updating is handled separately, so ignore these):
            {profile_keys_str}
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
        chain = prompt | self.reasoning_model
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
                content = str(update.get('content', '')).strip().lower()
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

    def update_memory_from_categorizer(self, memory_updates: list, memory: dict):
        """Call the appropriate memory tool for each update object, updating memory in-place."""
        results = []
        current_memory = memory
        for update in memory_updates:
            mtype = update.get('type')
            if mtype == 'semantic':
                tool = self.memory_tools.get('update_semantic_memory_tool')
                if tool:
                    result = tool({
                        'content': update.get('content', ''),
                        'category': update.get('category', 'general'),
                        'metadata': update.get('metadata', {}),
                        'memory': current_memory
                    })
                    current_memory = result.get('memory', current_memory)
                    results.append(result)
            elif mtype == 'episodic':
                tool = self.memory_tools.get('store_episodic_memory_tool')
                if tool:
                    result = tool({
                        'interaction_type': update.get('interaction_type', ''),
                        'content': update.get('content', ''),
                        'reasoning_context': update.get('reasoning_context', ''),
                        'outcome': update.get('outcome', ''),
                        'metadata': update.get('metadata', {}),
                        'memory': current_memory
                    })
                    current_memory = result.get('memory', current_memory)
                    results.append(result)
            elif mtype == 'procedural':
                tool = self.memory_tools.get('update_procedural_memory_tool')
                if tool:
                    result = tool({
                        'rule_type': update.get('category', ''),
                        'rule_data': update.get('content', {}),
                        'memory': current_memory
                    })
                    current_memory = result.get('memory', current_memory)
                    results.append(result)
        return results, current_memory

    def llm_postprocess_response(self, tool_output, user_input, prompt=None):
        """Use the LLM to generate a conversational answer from the tool output and user input."""
        if settings.DEBUG:
            print(f"[DEBUG] LLM post-processing response: {tool_output} for user input: {user_input}")
        try:
            from langchain_core.prompts import ChatPromptTemplate
            if prompt:
                prompt = ChatPromptTemplate.from_messages(prompt)
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant. Given the following tool result and the user's question, answer as helpfully and conversationally as possible. If the tool result contains web search results, use only the most recent and explicit information from the top 5 results to answer fact-based questions (such as 'Who is the current US president?'). If there is any ambiguity or the answer is not explicit, say 'I cannot determine with certainty.' Always prefer the most recent, date-stamped, and explicit answer."),
                ("human", "Tool result: {tool_output}\n\nUser question: {user_input}\n\nAnswer:")
            ])
            chain = prompt | self.reasoning_model
            summary = chain.invoke({"tool_output": str(tool_output), "user_input": user_input})
            if hasattr(summary, 'content'):
                return summary.content
            return str(summary)
        except Exception as e:
            logger.error(f"Error in LLM post-processing: {str(e)}")
            return str(tool_output)

    def run(self, user_input: str, memory: dict, conversation: Optional[dict] = None, patient_profile: Optional[dict] = None) -> dict:
        """Run the supervisor workflow with user input."""
        try:
            # --- Semantic memory pre-check step with perfect match threshold ---
            search_tool = self.memory_tools.get('search_semantic_memory_tool')
            preface = None
            if search_tool:
                # Pass the memory dict to the search tool if it supports it
                search_result = search_tool({
                    'query': user_input,
                    'limit': 3,
                    'memory': memory  # Pass memory explicitly if tool supports it
                })
                results = search_result.get('results', [])
                if settings.DEBUG:
                    logger.info(f"[DEBUG] Semantic search results for '{user_input}': {results}")
                if results:
                    all_contents = "\n- ".join(r.get('content', '') for r in results)
                    memory_response = f"I found these in your memory:\n- {all_contents}"
                    # Use LLM to check if the memory is relevant to the user query
                    relevance_prompt = (
                        "You are an AI assistant. Given the user's question and the following retrieved memories, "
                        "determine if any of the memories directly answer or are relevant to the user's question. "
                        "If yes, respond with 'true'. If not, respond with 'false'."
                        "Make sure you provide an explantion for your answer."
                        "Example response: 'true, because the user's question is about the weather, and the retrieved memories are about the weather.'"
                        "User question: {user_input}\n"
                        "Retrieved memories: {all_contents}\n"
                        "Answer:"
                    )
                    from langchain_core.prompts import ChatPromptTemplate
                    prompt = ChatPromptTemplate.from_template(relevance_prompt)
                    chain = prompt | self.reasoning_model
                    relevance_result = chain.invoke({"user_input": user_input, "all_contents": all_contents})
                    relevance = str(relevance_result.content).strip().lower() if hasattr(relevance_result, 'content') else str(relevance_result).strip().lower()
                    if settings.DEBUG:
                        print(f"[DEBUG] Relevance result: {relevance}")
                    if 'true' in relevance:
                        return {"memory": memory}
                    # If not relevant, fall through to run the workflow as usual
                # Otherwise, proceed as normal
                if not results:
                    # LLM call to check if user_input is a valid fact
                    from langchain_core.prompts import ChatPromptTemplate
                    fact_check_prompt = ChatPromptTemplate.from_messages([
                        ("system", "You are a fact-checking assistant. Given a user input, determine if it is a valid, concrete fact (not a question, request, or vague statement). Respond with 'yes' or 'no' only."),
                        ("human", "User input: {user_input}\n\nAnswer:")
                    ])
                    fact_chain = fact_check_prompt | self.reasoning_model
                    fact_result = fact_chain.invoke({"user_input": user_input})
                    is_fact = True #str(fact_result.content).strip().lower() == 'yes'
                    if is_fact:
                        # LLM-powered memory categorization and update step
                        memory_updates = self.llm_memory_categorizer(user_input, memory)
                        logger.info(f"[DEBUG] Memory categorizer updates: {memory_updates}")
                        if memory_updates:
                            memory_results, memory = self.update_memory_from_categorizer(memory_updates, memory)
                            logger.info(f"[DEBUG] Memory update results: {memory_results}")
                            preface = "Added to memory."
                    else:
                        preface = None
            else:
                preface = None
            # --- END semantic memory pre-check ---

            # Create initial state
            initial_state = {
                "messages": [
                    {"role": "user", "content": user_input}
                ],
                "memory": memory
            }
            
            # Create config
            from langchain_core.runnables import RunnableConfig
            config: RunnableConfig = {
                "configurable": {
                    "thread_id": "default_thread",
                    "checkpoint_ns": "supervisor_workflow"
                }
            }
            
            # Run the workflow
            result = self.app.invoke(initial_state, config=config)
            
            if result is None:
                logger.error("Supervisor workflow returned None as result.")
                return {"memory": memory, "error": "I apologize, but I encountered an internal error (no result)."}
            messages = result.get("messages", [])
            if settings.DEBUG:
                print(f"[DEBUG] Messages: {messages}")
            
            final_response = None
            last_agent = None
            
            # Prefer final_response if present
            if result.get("final_response"):
                logger.info(f"[DEBUG] Supervisor: Using result['final_response']: {result['final_response']}")
                final_response = result["final_response"]
            else:
                # Find the final response from processed messages
                for message in reversed(messages):
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

                if not final_response:
                    logger.info("[DEBUG] Supervisor: No final_response found in messages, using fallback.")
                    final_response = result.get("final_response", "No response generated")
            # LLM post-processing for user-friendly answer
            logger.info(f"[DEBUG] Supervisor: Pre-LLM postprocess final_response: {final_response}")
            #------SPED UP HERE-1-----
            conversational_response = self.llm_postprocess_response(final_response, user_input)
            #------SPED UP HERE-1-----
            logger.info(f"[DEBUG] Supervisor: Post-LLM postprocess conversational_response: {conversational_response}")
            logger.info(f"[EXPLICIT DEBUG] Supervisor about to return: type={type(conversational_response)}, value={conversational_response}")
            updated_memory = result.get("memory", memory)
            if 'preface' in locals() and preface:
                return {"memory": updated_memory, "response": f"{preface}\n{str(conversational_response)}"}
            return {"memory": updated_memory, "response": str(conversational_response)}
        except Exception as e:
            logger.error(f"Error running supervisor workflow: {str(e)}")
            return {"memory": memory, "error": f"I apologize, but I encountered an error: {str(e)}"}

    def chat(self, debug: bool = False):
        """Start interactive chat session with in-memory memory dict."""
        self.debug_mode = debug
        if settings.DEBUG:
            print("DEBUG MODE: Detailed logging enabled")
            print("Enhanced LangGraph Supervisor AI Agent is ready! Type 'quit' to exit.")
            print("You can:")
            print("- Ask questions about your patient profile")
            print("- Update your patient information")
            print("- Read/write files")
            print("- Search the web")
            print("- Summarize text")
            print("- Query the database")
            print()
        memory = {"semantic": [], "episodes": [], "procedural": {}}
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    if settings.DEBUG:
                        print("Goodbye!")
                    break
                if user_input.lower() == 'debug':
                    self.debug_mode = not self.debug_mode
                    if settings.DEBUG:
                        print(f"Debug mode: {'ON' if self.debug_mode else 'OFF'}")
                    continue
                if not user_input:
                    continue
                result = self.run(user_input, memory)
                # Update memory with the latest returned value
                memory = result.get("memory", memory)
                if "response" in result:
                    print(f"Agent: {result['response']}")
                elif "error" in result:
                    print(f"Agent (error): {result['error']}")
                else:
                    print(f"Agent: (no response)")
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
                if settings.DEBUG:
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
        if settings.DEBUG:
            import traceback
            print(f"Full traceback:\n{traceback.format_exc()}")

if __name__ == "__main__":
    main() 