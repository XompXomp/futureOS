# Migration Guide: LangChain to LangGraph

This document outlines the migration from the original LangChain backend to the new LangGraph implementation.

## Key Differences

### 1. Architecture

**LangChain (Original)**
```python
# Single agent with tools
agent = initialize_agent(
    tools=all_tools,
    llm=self.llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=self.memory,
    verbose=settings.VERBOSE
)
```

**LangGraph (New)**
```python
# Stateful workflow with explicit nodes
workflow = StateGraph(PatientState)
workflow.add_node("process_input", process_input)
workflow.add_node("retrieve_memory", retrieve_memory)
workflow.add_node("route_to_tools", route_to_tools)
# ... more nodes
```

### 2. Memory System

**LangChain (Original)**
```python
# Simple conversation buffer
self.memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    return_messages=True,
    k=10
)
```

**LangGraph (New)**
```python
# Advanced semantic and episodic memory
memory = Memory(
    semantic_k=settings.MEMORY_RETRIEVAL_K,
    episodic_k=settings.MEMORY_RETRIEVAL_K,
    similarity_threshold=settings.MEMORY_SIMILARITY_THRESHOLD
)
```

### 3. Tool Implementation

**LangChain (Original)**
```python
# Tools as functions
@tool
def read_patient_profile(query: str) -> str:
    # Tool implementation
    pass
```

**LangGraph (New)**
```python
# Tools as graph nodes
def read_patient_profile(state: Dict[str, Any]) -> Dict[str, Any]:
    # Tool implementation with state management
    tool_results = state.get("tool_results", [])
    tool_results.append({
        "tool": "read_patient_profile",
        "output": "Profile loaded successfully"
    })
    state["tool_results"] = tool_results
    return state
```

### 4. State Management

**LangChain (Original)**
- Implicit state management
- Limited control over data flow
- Memory handled internally

**LangGraph (New)**
```python
class PatientState(TypedDict):
    messages: List[BaseMessage]
    user_input: str
    patient_profile: Dict[str, Any]
    tool_results: List[Dict[str, Any]]
    memory: Memory
    retrieved_context: List[Dict[str, Any]]
    # ... more state fields
```

## Benefits of Migration

### 1. Better Memory Management
- **Semantic Memory**: Stores and retrieves information based on meaning
- **Episodic Memory**: Maintains conversation history and events
- **Configurable Retrieval**: Adjustable similarity thresholds and retrieval parameters

### 2. Explicit State Management
- **Clear Data Flow**: State transitions are explicit and traceable
- **Better Debugging**: Easy to inspect state at any point
- **Predictable Behavior**: State changes are controlled and documented

### 3. Modular Design
- **Reusable Nodes**: Graph nodes can be reused across workflows
- **Easy Extension**: Adding new tools is straightforward
- **Better Testing**: Individual nodes can be tested in isolation

### 4. Advanced Workflow Control
- **Conditional Routing**: Smart routing based on user input
- **Error Handling**: Robust error handling at each step
- **Iteration Control**: Explicit control over workflow iterations

## Migration Steps

### 1. Install Dependencies
```bash
pip install langgraph==0.2.40 langmem==0.1.0
```

### 2. Update Configuration
- Add LangMem settings to `config/settings.py`
- Configure memory retrieval parameters
- Set up similarity thresholds

### 3. Convert Tools
- Transform LangChain tools to graph nodes
- Add state management to tool functions
- Implement proper error handling

### 4. Create Workflow
- Define state schema
- Create graph nodes
- Set up conditional routing
- Add edges between nodes

### 5. Update Main Application
- Replace agent initialization with graph compilation
- Update state management
- Implement proper error handling

## File Structure Comparison

**LangChain Structure**
```
backend/
├── main.py              # Single agent file
├── tools/               # Tool definitions
├── modules/             # Utility modules
└── config/              # Configuration
```

**LangGraph Structure**
```
backend_langgraph/
├── main.py              # Entry point
├── graph/               # Workflow definitions
├── nodes/               # Graph nodes
├── tools/               # Tool implementations
├── state/               # State schema
├── config/              # Configuration
└── utils/               # Utilities
```

## Performance Improvements

### 1. Memory Efficiency
- Semantic memory reduces redundant storage
- Episodic memory provides context without full history
- Configurable retrieval reduces memory usage

### 2. Response Quality
- Better context retrieval from semantic memory
- More relevant information from episodic memory
- Improved tool routing based on user intent

### 3. Scalability
- Modular design allows easy extension
- State management scales with complexity
- Clear separation of concerns

## Testing the Migration

1. **Structure Test**: Run `python test_structure.py`
2. **Import Test**: Verify all modules can be imported
3. **Functionality Test**: Test basic patient profile operations
4. **Memory Test**: Verify semantic and episodic memory
5. **Integration Test**: Test complete workflows

## Next Steps

1. **Install Dependencies**: Set up the new environment
2. **Configure Memory**: Set up LangMem parameters
3. **Test Basic Operations**: Verify patient profile operations
4. **Add Advanced Features**: Implement LLM-based tool routing
5. **Optimize Performance**: Fine-tune memory and routing parameters 