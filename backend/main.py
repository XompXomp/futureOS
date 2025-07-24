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

# --- Define the state structure properly ---
class AgentState(TypedDict):
    input: str
    memory: Dict
    patientProfile: Dict
    # Add other fields that your tools might return
    results: Optional[str]
    error: Optional[str]
    user_input: Optional[str]
    query: Optional[str]
    content: Optional[str]
    final_answer: Optional[str]
    source: Optional[str]

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

# --- Router function for conditional edges ---
def route_to_agent(state: AgentState) -> str:
    """
    This function is used specifically for conditional edge routing.
    It receives the state and returns the agent name as a string.
    """
    print(f"DEBUG - route_to_agent received state keys: {list(state.keys())}")
    print(f"DEBUG - route_to_agent input: {state.get('input', 'NO INPUT')}")
    
    user_input = state.get('input', '')
    user_lower = user_input.lower()
    
    # # Simple conversational text patterns
    # simple_text_patterns = [
    #     'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
    #     'how are you', 'thank you', 'thanks', 'bye', 'goodbye', 'see you',
    #     'ok', 'okay', 'yes', 'no', 'sure', 'alright', 'nice', 'great',
    #     'cool', 'awesome', 'perfect', 'wonderful'
    # ]
    
    # # Check for simple conversational patterns
    # if any(pattern in user_lower for pattern in simple_text_patterns):
    #     print("DEBUG - Routing to text (simple conversation)")
    #     return 'text'
    
    # # Patient-related keywords
    # if any(keyword in user_lower for keyword in ['name', 'age', 'profile', 'patient', 'update', 'my', 'i am']):
    #     print("DEBUG - Routing to patient")
    #     return 'patient'
        
    # # Web search keywords
    # if any(keyword in user_lower for keyword in ['search', 'google', 'who is', 'what is', 'current', 'latest', 'news']):
    #     print("DEBUG - Routing to web")
    #     return 'web'# # Check for simple conversational patterns
    # if any(pattern in user_lower for pattern in simple_text_patterns):
    #     print("DEBUG - Routing to text (simple conversation)")
    #     return 'text'
    
    # # Patient-related keywords
    # if any(keyword in user_lower for keyword in ['name', 'age', 'profile', 'patient', 'update', 'my', 'i am']):
    #     print("DEBUG - Routing to patient")
    #     return 'patient'
        
    # # Web search keywords
    # if any(keyword in user_lower for keyword in ['search', 'google', 'who is', 'what is', 'current', 'latest', 'news']):
    #     print("DEBUG - Routing to web")
    #     return 'web'
        
    # Fall back to LLM routing for ambiguous cases
    try:
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
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a strict router for a healthcare AI system. Based on the user's input, choose exactly one agent to handle the request.\n"
                "Available agents: text, patient, web\n\n"
                "Routing rules:\n"
                "1. Use 'text' for simple greetings, chit-chat, casual conversations, or general questions that don't need tools.\n"
                "   Examples:\n"
                "   - 'Hi'\n"
                "   - 'Tell me a joke'\n"
                "   - 'What is your name?'\n"
                "   - 'Explain photosynthesis'\n\n"
                "2. Use 'patient' for anything related to the patient’s profile, such as their name, age, gender, allergies, medications, routines, appointments, health recommendations, or personal history.\n"
                "   Examples:\n"
                "   - 'What medications is the patient taking?'\n"
                "   - 'Update sleep quality to poor'\n"
                "   - 'Does John have any allergies?'\n"
                "   - 'Add walking to daily checklist'\n\n"
                "3. Use 'web' for real-time or fact-based queries that may change over time and require a current search.\n"
                "   Examples:\n"
                "   - 'Nvidia stock price'\n"
                "   - 'Current bitcoin value'\n"
                "   - 'Latest news on diabetes research'\n"
                "   - 'Weather in Dubai today'\n"
                "   - 'Population of China'\n"
                "   - 'COVID-19 cases in US'\n\n"
                "Output ONLY one of: text, patient, web — and nothing else."
            ))
            ,
            ("human", "User input: {user_input}")
        ])
        
        chain = prompt | llm
        result = chain.invoke({"user_input": user_input})
        agent_name = str(result.content).strip().lower()
        
        if agent_name in ['text', 'patient', 'web']:
            print(f"DEBUG - LLM routing to {agent_name}")
            return agent_name
            
    except Exception as e:
        logger.error(f"Error in LLM routing: {str(e)}")
    
    # Default fallback to text for safety
    print("DEBUG - Default routing to text")
    return 'text'

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
    memory = state.get('memory', {})
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
        all_contents = "\n- ".join(r.get('content', '') for r in results)
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
            "Should the following user input be stored in semantic memory? Only store if it is a meaningful fact, preference, or something about the user. Respond 'true' or 'false'.\nUser input: {user_input}\nAnswer:"
        )
        filter_chain = filter_prompt | llm
        filter_result = filter_chain.invoke({"user_input": user_input})
        should_store = str(filter_result.content).strip().lower()
        if 'true' in should_store:
            update_state = state.copy()
            update_state['content'] = user_input
            update_state['category'] = 'general'
            updated = tools['update_semantic_memory'](update_state)
            state['memory'] = updated.get('memory', memory)
            print("DEBUG - Semantic memory updated with new fact/preference (after LLM filter)")
        else:
            print("DEBUG - User input not meaningful for semantic memory, not storing (after LLM filter).")
        
        return state
    # 5. If no results, check if input is meaningful to store
    filter_prompt = ChatPromptTemplate.from_template(
        "Should the following user input be stored in semantic memory? Only store if it is a meaningful fact, preference, or something about the user. Respond 'true' or 'false'.\nUser input: {user_input}\nAnswer:"
    )
    filter_chain = filter_prompt | llm
    filter_result = filter_chain.invoke({"user_input": user_input})
    should_store = str(filter_result.content).strip().lower()
    if 'true' in should_store:
        update_state = state.copy()
        update_state['content'] = user_input
        update_state['category'] = 'general'
        updated = tools['update_semantic_memory'](update_state)
        state['memory'] = updated.get('memory', memory)
        print("DEBUG - Semantic memory updated with new fact/preference (no prior results)")
    else:
        print("DEBUG - User input not meaningful for semantic memory, not storing (no prior results).")
    return state

# --- Build the LangGraph workflow ---
def build_workflow():
    # Use the typed state
    graph = StateGraph(AgentState)
    
    graph.add_node('semantic_precheck', semantic_memory_precheck_node)
    graph.add_node('text', text_node)
    graph.add_node('patient', patient_node)
    graph.add_node('web', web_node)
    graph.add_node('postprocess', postprocess_node)
    
    # Set semantic precheck as entry
    graph.set_entry_point('semantic_precheck')

    # Single conditional edge from semantic_precheck
    def precheck_conditional(state):
        if state.get('final_answer'):
            return 'postprocess'
        else:
            # Use route_to_agent to determine which node to go to
            return route_to_agent(state)
    
    graph.add_conditional_edges('semantic_precheck', precheck_conditional, {
    'text': 'text',
    'patient': 'patient',
    'web': 'web',
    'postprocess': 'postprocess'
})

    # Both patient and web nodes go to postprocess
    graph.add_edge('text', 'postprocess')
    graph.add_edge('patient', 'postprocess')
    graph.add_edge('web', 'postprocess')
    graph.add_edge('postprocess', END)
    
    return graph.compile()

def run_agent_workflow(user_input, memory, patient_profile):
    """
    Run the workflow in 'server' mode: takes user_input, memory, patient_profile and returns the updated result state.
    """
    workflow = build_workflow()
    initial_state: AgentState = {
        'input': user_input,
        'memory': memory,
        'patientProfile': patient_profile,
        'results': None,
        'error': None,
        'user_input': None,
        'query': None,
        'content': None,
        'final_answer': None
    }
    result = workflow.invoke(initial_state)
    return result