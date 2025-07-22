# Main agent orchestrator 

import os
import json
from typing import Optional, Any, Dict, TypedDict
from config.settings import settings
from tools.patient_tools import create_patient_tools
from tools.text_tools import create_text_tools
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
    summary: Optional[str]
    keywords: Optional[str]
    results: Optional[str]
    error: Optional[str]
    user_input: Optional[str]
    text: Optional[str]
    query: Optional[str]
    content: Optional[str]
    final_answer: Optional[str]

def select_tool_llm(user_input: str, tool_names: list) -> str:
    """Use a small LLM call to select the tool name based on user_input and available tool_names."""
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
    tool_list = ', '.join(tool_names)
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            f"You are a tool selector for an AI agent. Given a user input, select the most appropriate tool to run from the following list: {tool_list}.\n"
            "Return ONLY the tool name.\n"
            "EXAMPLES:\n"
            "User: What is my name?\nOutput: read_patient_profile\n"
            "User: Update my age to 35\nOutput: update_patient_profile\n"
            "User: Summarize this text: ...\nOutput: summarize_text\n"
            "User: Extract keywords from this article\nOutput: extract_keywords\n"
            "User: Just say hi\nOutput: respond_conversationally\n"
        )),
        ("human", "User input: {user_input}")
    ])
    chain = prompt | llm
    result = chain.invoke({"user_input": user_input})
    tool_name = str(result.content).strip()
    if tool_name in tool_names:
        return tool_name
    return tool_names[0]  # fallback

# --- Tool node wrappers with LLM-based tool selection ---
def patient_node(state: AgentState) -> AgentState:
    print(f"DEBUG - patient_node received state keys: {list(state.keys())}")
    print(f"DEBUG - patient_node input: {state.get('input', 'NO INPUT')}")
    try:
        user_input = state.get('input', '')
        tools = {t.name: t.func for t in create_patient_tools()}
        tool_names = list(tools.keys())
        tool_to_run = select_tool_llm(user_input, tool_names)
        new_state = state.copy()
        if tool_to_run == 'update_patient_profile':
            new_state['user_input'] = state['input']
        result = tools[tool_to_run](new_state)
        if isinstance(result, dict):
            new_state.update(result)
        else:
            new_state['error'] = f"Patient tool returned unexpected type: {type(result)}"
        print(f"DEBUG - patient_node returning state keys: {list(new_state.keys())}")
        return new_state
    except Exception as e:
        logger.error(f"Error in patient_node: {str(e)}")
        new_state = state.copy()
        new_state['error'] = f"Patient node error: {str(e)}"
        return new_state

def text_node(state: AgentState) -> AgentState:
    print(f"DEBUG - text_node received state keys: {list(state.keys())}")
    print(f"DEBUG - text_node input: {state.get('input', 'NO INPUT')}")
    try:
        user_input = state.get('input', '')
        tools = {t.name: t.func for t in create_text_tools()}
        tool_names = list(tools.keys())
        tool_to_run = select_tool_llm(user_input, tool_names)
        new_state = state.copy()
        new_state['text'] = state['input']
        result = tools[tool_to_run](new_state)
        if isinstance(result, dict):
            new_state.update(result)
            if tool_to_run == 'summarize_text':
                summary = result.get('summary')
                if summary:
                    new_state['final_answer'] = summary
            elif tool_to_run == 'extract_keywords':
                keywords = result.get('keywords')
                if keywords:
                    new_state['final_answer'] = keywords
            elif tool_to_run == 'respond_conversationally':
                response = result.get('response')
                if response:
                    new_state['final_answer'] = response
        else:
            new_state['error'] = f"Text tool returned unexpected type: {type(result)}"
        print(f"DEBUG - text_node returning state keys: {list(new_state.keys())}")
        return new_state
    except Exception as e:
        logger.error(f"Error in text_node: {str(e)}")
        new_state = state.copy()
        new_state['error'] = f"Text node error: {str(e)}"
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
        else:
            new_state['error'] = f"Web tool returned unexpected type: {type(result)}"
            
        print(f"DEBUG - web_node returning state keys: {list(new_state.keys())}")
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
    
    # Simple rule-based routing first (faster than LLM)
    user_lower = user_input.lower()
    
    # Patient-related keywords
    if any(keyword in user_lower for keyword in ['name', 'age', 'profile', 'patient', 'update', 'my', 'i am']):
        print("DEBUG - Routing to patient")
        return 'patient'
    
    # Text processing keywords  
    if any(keyword in user_lower for keyword in ['summarize', 'summary', 'keywords', 'extract']):
        print("DEBUG - Routing to text")
        return 'text'
        
    # Web search keywords
    if any(keyword in user_lower for keyword in ['search', 'google', 'who is', 'what is', 'current', 'latest', 'news']):
        print("DEBUG - Routing to web")
        return 'web'
        
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
                "You are a strict router for a healthcare AI system. Given a user input, decide which agent should handle it.\n"
                "Available agents: patient, text, web.\n"
                "- Use 'patient' for anything about patient profile, name, age, gender, or updates.\n"
                "- Use 'text' for summarization, keyword extraction, or general text analysis.\n"
                "- Use 'web' for web search, news, current events, or fact-based queries.\n"
                "Output ONLY one of: patient, text, web. No explanation.\n"
            )),
            ("human", "User input: {user_input}")
        ])
        
        chain = prompt | llm
        result = chain.invoke({"user_input": user_input})
        agent_name = str(result.content).strip().lower()
        
        if agent_name in ['patient', 'text', 'web']:
            print(f"DEBUG - LLM routing to {agent_name}")
            return agent_name
            
    except Exception as e:
        logger.error(f"Error in LLM routing: {str(e)}")
    
    # Default fallback
    print("DEBUG - Default routing to text")
    return 'text'

def postprocess_response(user_input, tool_output):
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
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a helpful assistant. Given the user's question and the tool output, answer as concisely and directly as possible. "
            "If the tool output is a patient profile, answer only the specific question asked (e.g., just the name, just the medications). "
            "If the tool output is a list of web search results, use only the most relevant result to answer the user's question. "
            "Do not repeat the entire profile or all results unless explicitly asked. "
            "If the answer is not found, say so clearly."
        )),
        ("human", "User question: {user_input}\nTool output: {tool_output}\nAnswer:")
    ])
    chain = prompt | llm
    result = chain.invoke({"user_input": user_input, "tool_output": json.dumps(tool_output, indent=2)})
    return str(result.content).strip()

# --- Post-processing node for final answer ---
def postprocess_node(state: AgentState) -> AgentState:
    user_input = state.get('input', '')
    answer = postprocess_response(user_input, state)
    new_state = state.copy()
    new_state['final_answer'] = answer
    print("postprocess_node state\n", new_state)
    return new_state

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

    # 1. Flatten patient profile keys and check for match
    def flatten_keys(d, prefix=""):
        keys = []
        for k, v in d.items():
            full_key = f"{prefix}.{k}" if prefix else k
            keys.append(full_key)
            if isinstance(v, dict):
                keys.extend(flatten_keys(v, full_key))
        return keys
    profile_keys = flatten_keys(patient_profile)
    user_input_lower = user_input.lower()
    if any(pk.replace('.', ' ').lower() in user_input_lower for pk in profile_keys):
        print("DEBUG - Skipping semantic memory (patient profile field detected)")
        return state  # Pass state unchanged

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
    
    # Add all the nodes
    graph.add_node('semantic_precheck', semantic_memory_precheck_node)
    graph.add_node('patient', patient_node)
    graph.add_node('text', text_node)
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
        'patient': 'patient',
        'text': 'text', 
        'web': 'web',
        'postprocess': 'postprocess'
    })

    # Only patient and web nodes go to postprocess, text goes directly to END
    graph.add_edge('patient', 'postprocess')
    graph.add_edge('web', 'postprocess')
    graph.add_edge('text', END)
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
        'summary': None,
        'keywords': None,
        'results': None,
        'error': None,
        'user_input': None,
        'text': None,
        'query': None,
        'content': None,
        'final_answer': None
    }
    result = workflow.invoke(initial_state)
    return result

# --- Main chat loop ---
def main():
    try:
        LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "utils", "logs")
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        workflow = build_workflow()
        
        print("AI Agent (LangGraph) is ready! Type 'quit' to exit.")
        print("You can:")
        print("- Ask questions about your patient profile")
        print("- Summarize text or extract keywords")
        print("- Search the web for information")
        print()
        
        # Initialize persistent state
        memory = {"semantic": [], "episodes": [], "procedural": {}}
        patient_profile = {
            "uid": "abc123",
            "name": "John Doe",
            "age": 30,
            "bloodType": "O+",
            "allergies": ["Penicillin", "Peanuts"],
            "treatment": {
                "medicationList": ["Aspirin 100mg", "Metformin 500mg"],
                "dailyChecklist": ["Take medication", "30 min walk", "Check blood pressure"],
                "appointment": "2024-08-01T10:30:00Z",
                "recommendations": ["Reduce salt intake", "Increase water consumption"],
                "sleepHours": 8,
                "sleepQuality": "good"
            }
        }
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("Goodbye!")
                    break
                    
                if not user_input:
                    continue
                
                # Create initial state with all necessary data
                initial_state: AgentState = {
                    'input': user_input,
                    'memory': memory,
                    'patientProfile': patient_profile,
                    'summary': None,
                    'keywords': None,
                    'results': None,
                    'error': None,
                    'user_input': None,
                    'text': None,
                    'query': None,
                    'content': None,
                    'final_answer': None
                }
                
                print(f"DEBUG - Invoking workflow with state keys: {list(initial_state.keys())}")
                print(f"DEBUG - Input: {user_input}")
                
                # Invoke the workflow
                result = workflow.invoke(initial_state)
                
                print(f"DEBUG - Workflow returned state keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                
                # Update persistent state from result
                if isinstance(result, dict):
                    memory = result.get('memory', memory)
                    patient_profile = result.get('patientProfile', patient_profile)
                    
                    # Print a helpful response based on what's available in result
                    if result.get('error'):
                        print(f"\nAgent (error): {result['error']}")
                    elif result.get('final_answer'):
                        print(f"\nAgent: {result['final_answer']}")
                    else:
                        # Fallback - print available keys for debugging
                        available_keys = [k for k, v in result.items() if v is not None and k not in ['input', 'user_input', 'text', 'query', 'content']]
                        if available_keys:
                            print(f"\nAgent: Operation completed. Available data: {available_keys}")
                        else:
                            print(f"\nAgent: Operation completed.")
                else:
                    print(f"\nAgent: Unexpected result type: {type(result)}")
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Error in chat loop: {str(e)}")
                print(f"Error processing request: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        print(f"Failed to start agent: {str(e)}")

if __name__ == "__main__":
    main()