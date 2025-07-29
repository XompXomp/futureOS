# Main agent orchestrator 

import os
import json
from typing import Optional, Any, Dict, TypedDict
from config.settings import settings
from tools.patient_tools import create_patient_tools
from tools.web_tools import create_web_tools
from utils.logging_config import logger
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
import requests
from datetime import datetime
import websockets
from langchain_core.runnables.graph_mermaid import draw_mermaid_png
from IPython.display import Image, display
import time

# --- Websocket function to send messages to Unmute ---
def send_message_to_unmute(text: str, patient_profile: dict) -> bool:
    """
    Send a message to Unmute via websocket.
    Returns True if successful, False otherwise.
    """
    try:
        # Get Unmute websocket URL from settings or use default
        unmute_url = getattr(settings, "UNMUTE_WEBSOCKET_URL", "ws://172.22.225.138:11000/v1/realtime")
        
        import asyncio
        
        async def send_message():
            async with websockets.connect(unmute_url, subprotocols=['realtime']) as websocket:
                message = {
                    "type": "conversation.item.input_text",
                    "text": text,
                    "patientProfile": patient_profile
                }
                
                await websocket.send(json.dumps(message))
        
        # Run the async function
        asyncio.run(send_message())
        
        print(f"DEBUG - Successfully sent message to Unmute: {text}")
        return True
        
    except Exception as e:
        print(f"DEBUG - Failed to send message to Unmute: {str(e)}")
        return False

# --- Define the state structure properly ---
class AgentState(TypedDict):
    input: str
    memory: list
    patientProfile: dict
    updates: list
    final_answer: Optional[str]
    source: Optional[str]
    error: Optional[str]
    insights: Optional[str]
    route_tag: Optional[str]

def select_tool_llm(user_input: str, tool_metadata: list[dict]) -> str:
    """Use an LLM to select the best tool based on user input and tool descriptions."""
    if getattr(settings, "USE_OLLAMA", False):
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

    from langchain_core.prompts import ChatPromptTemplate

    # Build tool list string for the prompt
    tool_list_str = "\n".join(
        f"- {tool['name']}: {tool['description']}" for tool in tool_metadata
    )
    tool_names = [tool['name'] for tool in tool_metadata]

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a tool selector for an AI agent. Given a user input, select the most appropriate tool "
            "to run from the following list. Use the descriptions to understand the purpose of each tool.\n\n"
            "Available tools:\n"
            "{tool_list}\n\n"
            "Return ONLY the tool name.\n\n"
            "EXAMPLES:\n"
            "User: What is my name?\nOutput: read_patient_profile\n"
            "User: Update my age to 35\nOutput: update_patient_profile\n"
            "User: I usually sleep 8 hours every night\nOutput: update_patient_profile\n"
            "User: What are my medications?\nOutput: read_patient_profile\n"
        )),
        ("human", "User input: {user_input}")
    ])

    chain = prompt | llm
    result = chain.invoke({
        "user_input": user_input,
        "tool_list": tool_list_str
    })

    tool_name = str(result.content).strip()

    if tool_name in tool_names:
        return tool_name
    return tool_names[0]  # fallback to the first tool


# --- Text node for simple conversational responses ---
def text_node(state: AgentState) -> AgentState:
    """Handle simple conversational text that doesn't require tools - just pass through"""
    print(f"DEBUG - text_node received state keys: {list(state.keys())}")
    print(f"DEBUG - text_node input: {state.get('input', 'NO INPUT')}")
    print("DEBUG - text_node doing nothing, just passing state through")
    
    # Simply return the state unchanged - no processing needed
    return state

# --- Helper functions for change tracking ---
def deep_compare_dicts(before: dict, after: dict, path: str = "") -> list:
    """Recursively compare two dictionaries and return list of changes"""
    changes = []
    
    # Get all keys from both dictionaries (top-level keys are the same)
    all_keys = before.keys()
    
    for key in all_keys:
        current_path = f"{path}.{key}" if path else key
        before_val = before.get(key)
        after_val = after.get(key)
        
        # Compare values
        if isinstance(before_val, dict) and isinstance(after_val, dict):
            # Recursively compare nested dictionaries
            nested_changes = deep_compare_dicts(before_val, after_val, current_path)
            changes.extend(nested_changes)
        elif isinstance(before_val, list) and isinstance(after_val, list):
            # Compare lists by length and content
            if len(before_val) != len(after_val) or before_val != after_val:
                # Determine if it's an addition or removal based on length
                if len(after_val) > len(before_val):
                    changes.append({
                        "path": current_path,
                        "before": before_val,
                        "after": after_val,
                        "type": "added"
                    })
                elif len(after_val) < len(before_val):
                    changes.append({
                        "path": current_path,
                        "before": before_val,
                        "after": after_val,
                        "type": "removed"
                    })
                else:
                    # Same length but different content (modified)
                    changes.append({
                        "path": current_path,
                        "before": before_val,
                        "after": after_val,
                        "type": "modified"
                    })
        else:
            # Compare primitive values
            if before_val != after_val:
                changes.append({
                    "path": current_path,
                    "before": before_val,
                    "after": after_val,
                    "type": "modified"
                })
    
    return changes

def generate_change_summary(changes: list) -> str:
    """Use LLM to generate a concise summary of changes"""
    if not changes:
        return ""
    
    # Prepare LLM
    if getattr(settings, "USE_OLLAMA", False):
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
    
    # Format changes for LLM
    changes_text = "\n".join([
        f"Field: {change['path']}\nBefore: {change['before']}\nAfter: {change['after']}\nType: {change['type']}\n"
        for change in changes
    ])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a healthcare assistant. Given a list of changes to a patient profile, "
            "generate a very brief, natural summary of what was updated. "
            "Use simple, clear language. Keep it under 20 words per change. "
            "Focus on what the user actually changed, not technical details.\n\n"
            "Examples:\n"
            "- 'Updated age from 25 to 26'\n"
            "- 'Added allergy to penicillin'\n"
            "- 'Changed sleep quality from good to poor'\n"
            "- 'Added walking to daily activities'\n\n"
            "Return only the summary text, nothing else."
        )),
        ("human", f"Changes made to patient profile:\n{changes_text}\nSummary:")
    ])
    
    chain = prompt | llm
    result = chain.invoke({"changes": changes_text})
    return str(result.content).strip()

# --- Tool node wrappers with LLM-based tool selection ---
def patient_node(state: AgentState) -> AgentState:
    print(f"DEBUG - patient_node received state keys: {list(state.keys())}")
    print(f"DEBUG - patient_node input: {state.get('input', 'NO INPUT')}")
    try:
        user_input = state.get('input', '')
        tools = create_patient_tools()

        # Prepare metadata and function mappings
        tool_metadata = [{"name": t.name, "description": t.description} for t in tools]
        tool_funcs = {t.name: t.func for t in tools}

        # LLM decides which tool to use
        tool_to_run = select_tool_llm(user_input, tool_metadata)

        # Safeguard: unknown tool fallback
        if tool_to_run not in tool_funcs:
            raise ValueError(f"Selected tool '{tool_to_run}' not found in available tools.")

        new_state = state.copy()

        # Store original patient profile for comparison
        original_profile = state.get('patientProfile', {}).copy()

        # Pass user_input if update tool is selected
        if tool_to_run == 'update_patient_profile':
            new_state['user_input'] = state['input']

        # Call the selected tool
        result = tool_funcs[tool_to_run](new_state)

        # Update state
        if isinstance(result, dict):
            new_state.update(result)
            if tool_to_run == 'update_patient_profile':
                new_state['final_answer'] = ""
        else:
            new_state['error'] = f"Patient tool returned unexpected type: {type(result)}"

        # Track changes if patient profile was updated
        if tool_to_run == 'update_patient_profile':
            updated_profile = new_state.get('patientProfile', {})
            changes = deep_compare_dicts(original_profile, updated_profile)
            
            if changes:
                # Generate summary of changes
                change_summary = generate_change_summary(changes)
                
                if change_summary:
                    # Add to updates field
                    current_updates = new_state.get('updates', [])
                    if not isinstance(current_updates, list):
                        current_updates = []
                    update_entry = {
                        # Format current time as DD_MM_YY_HH_MM
                        "datetime": datetime.now().strftime("%d_%m_%y_%H_%M"),
                        "text": change_summary
                    }
                    current_updates.append(update_entry)
                    new_state['updates'] = current_updates
                    
                    print(f"DEBUG - Added update: {change_summary}")

        print(f"DEBUG - patient_node returning state keys: {list(new_state.keys())}")
        new_state['source'] = 'patient'
        return new_state

    except Exception as e:
        logger.error(f"Error in patient_node: {str(e)}")
        new_state = state.copy()
        new_state['error'] = f"Patient node error: {str(e)}"
        return new_state

def web_node(state: AgentState) -> AgentState:
    """Handle web search operations"""
    print(f"DEBUG - web_node received state keys: {list(state.keys())}")
    print(f"DEBUG - web_node input: {state.get('input', 'NO INPUT')}")
    
    try:
        tools = {t.name: t.func for t in create_web_tools()}
        
        # Create a new state dict
        new_state = state.copy()
        new_state['query'] = state['input']
        
        result = tools['web_search'](new_state)
        
        # Update state with results
        if isinstance(result, dict):
            new_state.update(result)
            results = new_state.get('results')
            if results and isinstance(results, list) and len(results) > 0:
                new_state['final_answer'] = results[0].get('snippet', '')
            else:
                new_state['final_answer'] = ""
        else:
            new_state['error'] = f"Web tool returned unexpected type: {type(result)}"
            
        print(f"DEBUG - web_node returning state keys: {list(new_state.keys())}")
        new_state['source'] = 'web'
        return new_state
        
    except Exception as e:
        logger.error(f"Error in web_node: {str(e)}")
        new_state = state.copy()
        new_state['error'] = f"Web node error: {str(e)}"
        return new_state

# --- Router function for conditional edges (COMMENTED OUT - NO LONGER NEEDED) ---
# def route_to_agent(state: AgentState) -> str:
    """
    This function is used specifically for conditional edge routing.
    It receives the state and returns the agent name as a string.
    """
    # print(f"DEBUG - route_to_agent received state keys: {list(state.keys())}")
    # print(f"DEBUG - route_to_agent input: {state.get('input', 'NO INPUT')}")
    
    # user_input = state.get('input', '')
    # user_lower = user_input.lower()
        
    # # Fall back to LLM routing for ambiguous cases
    # try:
    #     if getattr(settings, "USE_OLLAMA", False):
    #         llm = ChatOllama(
    #             model=settings.OLLAMA_MODEL,
    #             base_url=settings.OLLAMA_BASE_URL,
    #             temperature=0.3
    #         )
    #     else:
    #         llm = ChatGroq(
    #             model=settings.LLM_MODEL,
    #             temperature=0.3
    #         )
    #     
    #     prompt = ChatPromptTemplate.from_messages([
    #         ("system", (
    #             "You are a strict router for a healthcare AI system. Based on the user's input, choose exactly one agent to handle the request.\n"
    #             "Available agents: text, patient, web\n\n"
    #             "Routing rules:\n"
    #             "1. Use 'text' for simple greetings, chit-chat, casual conversations, or general questions that don't need tools.\n"
    #             "   Examples:\n"
    #             "   - 'Hi'\n"
    #             "   - 'Tell me a joke'\n"
    #             "   - 'What is your name?'\n"
    #             "   - 'Explain photosynthesis'\n\n"
    #             "2. Use 'patient' for anything related to the patient’s profile, such as their name, age, gender, allergies, medications, routines, appointments, health recommendations, or personal history.\n"
    #             "   Examples:\n"
    #             "   - 'What medications is the patient taking?'\n"
    #             "   - 'Update sleep quality to poor'\n"
    #             "   - 'Does John have any allergies?'\n"
    #             "   - 'Add walking to daily checklist'\n\n"
    #             "3. Use 'web' for real-time or fact-based queries that may change over time and require a current search.\n"
    #             "   Examples:\n"
    #             "   - 'Nvidia stock price'\n"
    #             "   - 'Current bitcoin value'\n"
    #             "   - 'Latest news on diabetes research'\n"
    #             "   - 'Weather in Dubai today'\n"
    #             "   - 'Population of China'\n"
    #             "   - 'COVID-19 cases in US'\n\n"
    #             "Output ONLY one of: text, patient, web — and nothing else."
    #         ))
    #         ,
    #         ("human", "User input: {user_input}")
    #     ])
    #     
    #     chain = prompt | llm
    #     result = chain.invoke({"user_input": user_input})
    #     agent_name = str(result.content).strip().lower()
    #     if agent_name in ['text', 'patient', 'web']:
    #         print(f"DEBUG - LLM routing to {agent_name}")
    #         return agent_name
    # except Exception as e:
    #     logger.error(f"Error in LLM routing: {str(e)}")
    # 
    # # Default fallback to text for safety
    # print("DEBUG - Default routing to text")
    # return 'text'

#     # New logic: use the tag set by the llm_tagger_node
#     return state.get('route_tag', 'text')

def postprocess_response(user_input, tool_output, source: str = None):
    if getattr(settings, "USE_OLLAMA", False):
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
    
    from langchain_core.prompts import ChatPromptTemplate

    # Conditional system prompt
    if source == 'patient' or source == 'memory':
        system_prompt = (
            "You are a helpful assistant. Given the user's question and the tool output, answer as concisely and directly as possible, "
            "ALWAYS in first person as if you are the patient. "
            "If the tool output is a patient profile, answer only the specific question asked (e.g., just the name, just the medications) in first person. "
            "If the tool output is a list of semantic memories, use only the most relevant and respond as the patient. "
            "If the answer is not found, say so clearly in first person."
        )
    else:  # For web and others
        system_prompt = (
            "You are a helpful assistant. Given the user's question and the tool output, answer concisely and accurately. "
            "Use third-person voice and avoid pretending to be the user. "
            "If the answer is not found in the output, say that clearly."
        )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "User question: {user_input}\nTool output: {tool_output}\nAnswer:")
    ])
    
    chain = prompt | llm
    result = chain.invoke({
        "user_input": user_input,
        "tool_output": json.dumps(tool_output, indent=2)
    })
    return str(result.content).strip()

# --- Post-processing node for final answer ---
def postprocess_node(state: AgentState) -> AgentState:
    user_input = state.get('input', '')
    source = state.get('source')  # could be 'web', 'patient', 'memory', etc.

    if state.get('final_answer'):
        answer = postprocess_response(user_input, state, source)
        new_state = state.copy()
        new_state['final_answer'] = answer
        return new_state
    else:
        return state

def is_input_about_patient_profile(user_input: str, patient_profile: dict) -> bool:
    # Choose model
    if getattr(settings, "USE_OLLAMA", False):
        llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0
        )
    else:
        llm = ChatGroq(
            model=settings.LLM_MODEL,
            temperature=0
        )

    # Flatten profile for context (show values too for better judgment)
    def flatten(d, prefix=""):
        items = []
        for k, v in d.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                items.extend(flatten(v, full_key))
            else:
                items.append(f"{full_key}: {v}")
        return items

    profile_context = "\n".join(flatten(patient_profile))

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a binary classifier. Determine whether the user's input is referencing any field or value "
            "in the provided patient profile. If yes, respond with 'yes'. Otherwise, respond with 'no'.\n"
            "Patient profile:\n{profile_context}\n\n"
            "Respond only 'yes' or 'no'. No explanation."
        )),
        ("human", "User input: {user_input}")
    ])

    chain = prompt | llm
    result = chain.invoke({
        "user_input": user_input,
        "profile_context": profile_context
    })

    response = result.content.strip().lower()
    return response == "yes"


def semantic_memory_precheck_node(state: AgentState) -> AgentState:
    """
    1. If user input is related to patient profile fields, skip this node.
    2. Semantic search for similar memories (top 3).
    3. If results found, use LLM to check if any are relevant.
        - If relevant, return those results as the answer.
        - If not relevant, use LLM to check if input is meaningful to store.
            - If yes, store in semantic memory.
            - If no, skip storing.
    4. If no results, use LLM to check if input is meaningful to store.
        - If yes, store in semantic memory.
        - If no, skip storing.
    """
    print(f"DEBUG - semantic_memory_precheck_node received state keys: {list(state.keys())}")
    user_input = state.get('input', '')
    patient_profile = state.get('patientProfile', {})
    memory = state.get('memory', [])
    state['source'] = 'memory'

    # 1. Flatten patient profile keys and check for match
    if is_input_about_patient_profile(user_input, patient_profile):
        print("DEBUG - Skipping semantic memory (patient-related input detected via LLM)")
        return state
        
    # 2. Semantic memory tools
    from tools.memory_tools import create_memory_tools
    tools = {t.name: t.func for t in create_memory_tools()}

    # 3. Search semantic memory
    search_state = state.copy()
    search_state['query'] = user_input
    search_state['limit'] = 3
    search_result = tools['search_semantic_memory'](search_state)
    results = search_result.get('results', [])

    # Prepare LLM
    from config.settings import settings
    if getattr(settings, "USE_OLLAMA", False):
        from langchain_ollama import ChatOllama
        llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.3
        )
    else:
        from langchain_groq import ChatGroq
        llm = ChatGroq(
            model=settings.LLM_MODEL,
            temperature=0.3
        )
    from langchain_core.prompts import ChatPromptTemplate

    # 4. If results found, check LLM relevance
    if results:
        all_contents = "\n- ".join(r.get('text', '') for r in results)
        prompt = ChatPromptTemplate.from_template(
            "Is any of the following memory relevant to the user's input? Respond 'true' or 'false'.\nUser: {user_input}\nMemory: {all_contents}\nAnswer:"
        )
        chain = prompt | llm
        relevance_result = chain.invoke({"user_input": user_input, "all_contents": all_contents})
        relevance = str(relevance_result.content).strip().lower()
        if 'true' in relevance:
            memory_response = f"I found these in your memory:\n- {all_contents}"
            state['final_answer'] = memory_response
            print("DEBUG - Relevant semantic memory found by LLM, returning early")
            return state
        # If not relevant, check if input is meaningful to store
        filter_prompt = ChatPromptTemplate.from_template(
            "Should the following user input be stored in semantic memory? Store if it's a meaningful fact, preference, about the user, OR contains medical-related information. Respond 'true' or 'false'.\nUser input: {user_input}\nAnswer:"
        )
        filter_chain = filter_prompt | llm
        filter_result = filter_chain.invoke({"user_input": user_input})
        should_store = str(filter_result.content).strip().lower()
        if 'true' in should_store:
            update_state = state.copy()
            updated = tools['update_semantic_memory'](update_state)
            state['memory'] = updated.get('memory', memory)
            print("DEBUG - Semantic memory updated with new fact/preference (after LLM filter)")
        else:
            print("DEBUG - User input not meaningful for semantic memory, not storing (after LLM filter).")
        
        return state
    # 5. If no results, check if input is meaningful to store
    filter_prompt = ChatPromptTemplate.from_template(
        "Should the following user input be stored in semantic memory? Store if it's a meaningful fact, preference, about the user, OR contains medical-related information. Respond 'true' or 'false'.\nUser input: {user_input}\nAnswer:"
    )
    filter_chain = filter_prompt | llm
    filter_result = filter_chain.invoke({"user_input": user_input})
    should_store = str(filter_result.content).strip().lower()
    if 'true' in should_store:
        update_state = state.copy()
        updated = tools['update_semantic_memory'](update_state)
        state['memory'] = updated.get('memory', memory)
        print("DEBUG - Semantic memory updated with new fact/preference (no prior results)")
    else:
        print("DEBUG - User input not meaningful for semantic memory, not storing (no prior results).")
    return state

# --- LLM Tagger Node (NEW) ---
def llm_tagger_node(state: AgentState) -> AgentState:
    user_input = state.get('input', '')

    # --- LLM-based classification (web, patient, text, medical, ui_change, add_treatment) ---
    if getattr(settings, "USE_OLLAMA", False):
        llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.3
        )
    else:
        llm = ChatGroq(
            model=settings.LLM_MODEL,
            temperature=0.3,
            api_key=os.getenv("GROQ_API_KEY")
        )
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a strict classifier for a healthcare AI system. "
            "Given a user input, classify it into exactly one of the following tags:\n\n"
            "TAGS:\n"
            
            "1. WEB: For real-time or fact-based queries that may change over time and require a current search. "
            "Examples: 'Nvidia stock price', 'Current bitcoin value', 'Latest news on diabetes research', "
            "'Weather in Dubai today', 'Population of China', 'COVID-19 cases in US'.\n"
            "Classify as WEB if the input is asking for current information, real-time data, or facts that may change over time.\n\n"
            
            "2. TEXT: For simple greetings, chit-chat, casual conversations, or general questions that don't need tools"
            "VERY IMPORTANT: USE for any requests related to adding, updating, or removing recommendations"
            "Examples: 'Hi', 'Tell me a joke', 'What is your name?', 'Explain photosynthesis', 'Add a recommendation to eat more iron rich food'.\n"
            "Classify as TEXT if the input is casual conversation, general knowledge questions, or recommendation-related requests.\n\n"
            
            "3. PATIENT: For anything related to the patient’s profile, such as their name, age, gender, allergies, medications, routines, appointments, or personal history."
            "VERY IMPORTANT: DO NOT use for any requests related to adding, updating, or removing recommendations"
            "Examples: 'What medications is the patient taking?', 'Update sleep quality to poor', 'Does John have any allergies?', 'Add walking to daily checklist'.\n"
            "Classify as PATIENT if the input is about reading or updating patient profile information (excluding recommendations).\n\n"
            
            "4. MEDICAL: For anything that is medical reasoning, verification, or critical treatment suggestions. "
            "This includes requests for medical advice, diagnosis, or complex medical questions that require domain-specific reasoning. "
            "Examples: 'Is this treatment safe for diabetes?', 'What are the contraindications for this drug?', "
            "'Should I combine these two medications?', 'Verify the diagnosis for this patient'.\n"
            "Classify as MEDICAL if the input is about medical reasoning, verification, or critical suggestions.\n\n"
            
            "5. UI_CHANGE: For requests related to changing the user interface, such as themes, layout, or settings. "
            "Examples: 'Change theme to dark mode', 'Switch to compact view', 'Open settings'.\n"
            "Classify as UI_CHANGE if the input is about UI themes or interface changes.\n\n"
            
            "6. ADD_TREATMENT: For requests to add a treatment of a particular type (e.g., 'Add physiotherapy to my plan'), "
            "but NOT for adding medications or anything else. "
            "Examples: 'Add physical therapy to my treatment plan', 'Include occupational therapy'. "
            "Do NOT use this tag for medication or general additions.\n\n"
            
            

            "Respond ONLY with one tag: WEB, TEXT, PATIENT, MEDICAL, UI_CHANGE, or ADD_TREATMENT. "
            "Do not explain your choice. Output only the tag."
        )),
        ("human", "User input: {user_input}")
    ])
    chain = prompt | llm
    result = chain.invoke({"user_input": user_input})
    tag = str(result.content).strip().lower()
    state['route_tag'] = tag  # This is what the agent will use

    return state

# --- Medical Reasoning Node (NEW) ---
def medical_reasoning_node(state: AgentState) -> AgentState:
    user_input = state.get('input', '')


    payload = {"prompt": user_input}

    try:
        response = requests.post(
            "http://172.22.225.49:8000/endpoint",
            json=payload,
            timeout=5
        )
        if response.ok:
            state['final_answer'] = response.text
        else:
            state['final_answer'] = f"API error: {response.status_code} {response.text}"
    except Exception as e:
        state['final_answer'] = f"API request failed: {e}"

    state['source'] = 'medical'
    return state

# --- Semantic Update Node (NEW) ---
def semantic_update_node(state: AgentState) -> AgentState:
    """
    Only updates semantic memory with the user input if appropriate.
    """
    user_input = state.get('input', '')
    memory = state.get('memory', [])

    # Import/create memory tools as in your other nodes
    from tools.memory_tools import create_memory_tools
    tools = {t.name: t.func for t in create_memory_tools()}

    # Use the same LLM as elsewhere
    if getattr(settings, "USE_OLLAMA", False):
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
    from langchain_core.prompts import ChatPromptTemplate

    # LLM: Should we store this in semantic memory?
    filter_prompt = ChatPromptTemplate.from_template(
        "Should the following user input be stored in semantic memory? Store if it's a meaningful fact, preference, about the user, OR contains medical-related information. Respond 'true' or 'false'.\nUser input: {user_input}\nAnswer:"
    )
    filter_chain = filter_prompt | llm
    filter_result = filter_chain.invoke({"user_input": user_input})
    should_store = str(filter_result.content).strip().lower()
    if 'true' in should_store:
        update_state = state.copy()
        updated = tools['update_semantic_memory'](update_state)
        state['memory'] = updated.get('memory', memory)
    return state

# --- Unmute Node (NEW) ---
# Using direct connection approach to avoid event loop conflicts

def unmute_node(state: AgentState) -> AgentState:
    """
    Side-effect node that streams to Unmute and frontend.
    Uses direct connection approach with response.create trigger.
    """
    user_input = state.get('input', '')
    patient_profile = state.get('patientProfile', {})
    route_tag = state.get('route_tag', '')
    
    # Determine text to send based on source
    source = state.get('source', '')
    
    # If source is medical or web, send the extra tag along with the result
    if source == 'medical' or source == 'web':
        text_to_send = state.get('final_answer', '')
        tag = 'extra'
    # If source is not medical or web, send the route tag along with the user input
    else:
        if route_tag in ['TEXT', 'PATIENT']:
            text_to_send = user_input
            tag = 'normal'
        elif route_tag == 'web':
            text_to_send = user_input
            tag = 'web'
        elif route_tag == 'medical':
            text_to_send = user_input
            tag = 'med'
        elif route_tag == 'add_treatment':
            text_to_send = user_input
            tag = 'addt'
        elif route_tag == 'ui_change':
            text_to_send = user_input
            tag = 'ui'
        else:
            text_to_send = user_input
            tag = 'normal'
    
    print(f"DEBUG - unmute_node: Starting streaming for '{text_to_send}'")
    
    # Use direct connection approach with response.create trigger
    try:
        import asyncio
        import websockets
        
        async def direct_unmute_connection():
            unmute_url = getattr(settings, "UNMUTE_WEBSOCKET_URL", "ws://172.22.225.138:11000/v1/realtime")
            
            async with websockets.connect(unmute_url, subprotocols=['realtime']) as websocket:
                print("✓ Connected to Unmute (direct)")
                
                # Session initialization
                session_message = {
                    "type": "session.update",
                    "session": {
                        "instructions": {
                            "type": "constant",
                            "text": "You are a helpful health assistant."
                        },
                        "voice": "unmute-prod-website/developer-1.mp3",
                        "allow_recording": True
                    }
                }
                await websocket.send(json.dumps(session_message))
                print("✓ Sent session initialization")
                
                await asyncio.sleep(1)
                
                # Send message
                
                prompt_message = {
                    "type": "conversation.item.input_text",
                    "text": text_to_send,
                    "patientProfile": patient_profile,
                    "tag": tag
                }
                if tag == 'extra':
                    prompt_message = {
                        "type": "conversation.item.input_text",
                        "text": text_to_send,
                        "tag": tag
                    }
                    
                await websocket.send(json.dumps(prompt_message))
                print(f"✓ Sent message: {prompt_message}")
                
                # ADD THIS: Send response generation trigger
                response_create_message = {
                    "type": "response.create"
                }
                await websocket.send(json.dumps(response_create_message))
                print(f"DEBUG - Sent response.create trigger")
                
                # Wait for response
                text_done = False
                audio_done = False
                start_time = time.time()
                
                while time.time() - start_time < 10:
                    try:
                        chunk = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        #print(f"✓ Received: {chunk}")
                        
                        try:
                            msg = json.loads(chunk)
                            msg_type = msg.get('type', '')
                            
                            if msg_type == 'unmute.response.text.delta.ready' and msg.get('delta'):
                                text_chunk = msg['delta']
                                print(f"DEBUG - Streaming text chunk: {text_chunk}")
                                # TODO: Send to frontend immediately
                                # await send_text_to_frontend(text_chunk)
                                
                            elif msg_type == 'response.audio.delta' and msg.get('delta'):
                                audio_chunk = msg['delta']
                                #print(f"DEBUG - Streaming audio chunk: {len(audio_chunk)} bytes")
                                # TODO: Send to frontend immediately
                                # await send_audio_to_frontend(audio_chunk)
                            
                            elif msg_type == 'response.text.done':
                                text_done = True
                                print(f"DEBUG - Text response done")
                            
                            elif msg_type == 'response.audio.done':
                                audio_done = True
                                print(f"DEBUG - Audio response done")
                            
                            if text_done and audio_done:
                                print(f"DEBUG - Response complete")
                                break
                                
                        except json.JSONDecodeError:
                            print(f"Non-JSON response: {chunk}")
                            
                    except asyncio.TimeoutError:
                        print("Timeout - no response received")
                        break
                    except websockets.exceptions.ConnectionClosed as e:
                        print(f"Connection closed: {e}")
                        break
                
                print("Direct connection completed")
        
        # Run the direct connection in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(direct_unmute_connection())
        finally:
            loop.close()
        
    except Exception as e:
        print(f"DEBUG - Direct connection failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Return None to terminate this branch (side-effect only)
    return None

# --- UI Change Node (NEW, optional) ---
def ui_change_node(state: AgentState) -> AgentState:
    # This node can set the function to be called on the frontend to handle the UI change
    state['final_answer'] = "[UI_CHANGE] Action required on frontend."
    state['source'] = 'ui'
    return state

# --- Processing Router Node (NEW) ---
def processing_router_node(state: AgentState) -> AgentState:
    """
    Routes to the appropriate processing node based on route_tag.
    This runs in parallel with the unmute livestream.
    """
    route_tag = state.get('route_tag', 'text')
    
    # Set a flag to indicate this is the processing path
    state['processing_path'] = True
    
    # Route to appropriate processing node
    if route_tag == 'text':
        state['next_node'] = 'semantic_precheck'
    elif route_tag == 'patient':
        state['next_node'] = 'patient'
    elif route_tag == 'web':
        state['next_node'] = 'web'
    elif route_tag == 'medical':
        state['next_node'] = 'semantic_update'  # First goes to semantic_update
    elif route_tag in ('ui_change', 'add_treatment'):
        state['next_node'] = 'ui_change'
    else:
        state['next_node'] = 'semantic_precheck'  # fallback
    
    return state

# --- Build the LangGraph workflow (UPDATED with Parallel Execution) ---
def build_workflow():
    graph = StateGraph(AgentState)
    graph.add_node('llm_tagger', llm_tagger_node)
    graph.add_node('unmute', unmute_node)
    graph.add_node('processing_router', processing_router_node)
    graph.add_node('semantic_precheck', semantic_memory_precheck_node)
    graph.add_node('patient', patient_node)
    graph.add_node('web', web_node)
    graph.add_node('medical', medical_reasoning_node)
    graph.add_node('semantic_update', semantic_update_node)
    graph.add_node('ui_change', ui_change_node)
    graph.add_node('postprocess', postprocess_node)

    graph.set_entry_point('llm_tagger')

    # Direct edges for parallel execution
    graph.add_edge('llm_tagger', 'unmute')
    graph.add_edge('llm_tagger', 'processing_router')

    # Processing router conditional
    def processing_conditional(state):
        next_node = state.get('next_node', 'semantic_precheck')
        return next_node

    graph.add_conditional_edges('processing_router', processing_conditional, {
        'semantic_precheck': 'semantic_precheck',
        'patient': 'patient',
        'web': 'web',
        'semantic_update': 'semantic_update',
        'ui_change': 'ui_change'
    })

    # Existing agentic workflow
    def precheck_conditional(state):
        if state.get('final_answer'):
            return 'postprocess'
        else:
            return 'end'

    graph.add_conditional_edges('semantic_precheck', precheck_conditional, {
        'postprocess': 'postprocess',
        'end': END
    })

    graph.add_edge('patient', END)
    graph.add_edge('web', 'postprocess')
    graph.add_edge('semantic_update', 'medical')
    graph.add_edge('medical', 'unmute')
    graph.add_edge('ui_change', END)
    
    # Postprocess conditional - go to unmute if source is web, else END
    def postprocess_conditional(state):
        source = state.get('source', '')
        if source == 'web':
            return 'unmute'
        else:
            return 'end'
    
    graph.add_conditional_edges('postprocess', postprocess_conditional, {
        'unmute': 'unmute',
        'end': END
    })

    return graph.compile()


def run_agent_workflow(user_input, memory, patient_profile, updates=None):
    """
    Run the workflow in 'server' mode: takes user_input, memory, patient_profile, updates and returns the updated result state.
    """
    workflow = build_workflow()

    mermaid_code = workflow.get_graph().draw_mermaid()
    print(mermaid_code)

    initial_state: AgentState = {
        'input': user_input,
        'memory': memory,
        'patientProfile': patient_profile,
        'updates': updates if updates is not None else [],
        'final_answer': None,
        'source': None,
        'error': None,
        'insights': None,
        'route_tag': None
    }
    result = workflow.invoke(initial_state)
    return result