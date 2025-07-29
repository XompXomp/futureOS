# Parallel Execution Flow Diagram

## LangGraph Parallel Execution Architecture

```mermaid
graph TD
    A[Frontend User Input] --> B[llm_tagger_node]
    
    B --> C{Parallel Execution}
    
    C --> D[unmute_node]
    C --> E[processing_router_node]
    
    D --> F[Background Thread]
    F --> G[Unmute Server]
    G --> H[Stream Text/Audio]
    H --> I[Frontend Real-time]
    D --> J[Return None - Branch Ends]
    
    E --> K{Route Based on Tag}
    
    K -->|text| L[semantic_precheck_node]
    K -->|patient| M[patient_node]
    K -->|web| N[web_node]
    K -->|medical| O[semantic_update_node]
    K -->|ui_change| P[ui_change_node]
    
    L --> Q{Has Answer?}
    Q -->|Yes| R[postprocess_node]
    Q -->|No| S[END]
    
    M --> S
    P --> S
    
    O --> T[medical_reasoning_node]
    T --> U[unmute_node]
    U --> V[Background Thread]
    V --> G
    
    N --> R
    R --> W{Source = web?}
    W -->|Yes| X[unmute_node]
    W -->|No| S
    
    X --> Y[Background Thread]
    Y --> G
    
    style D fill:#ff9999
    style J fill:#ffcccc
    style F fill:#ffcccc
    style H fill:#ffcccc
    style I fill:#ffcccc
    style U fill:#ff9999
    style X fill:#ff9999
    style Y fill:#ffcccc
```

## Key Features

### 🔄 **Parallel Execution**
- `llm_tagger_node` returns `{'unmute', 'processing_router'}` 
- Both nodes execute simultaneously
- No blocking between branches

### 🎤 **Unmute Side-Effects**
- `unmute_node` starts background thread
- Streams to Unmute server immediately
- Returns `None` to terminate branch
- No impact on main workflow

### ⚡ **Main Workflow Continuation**
- `processing_router` continues normal execution
- Routes to appropriate processing nodes
- Can call `unmute_node` again later if needed

### 🚀 **Multiple Unmute Calls**
- `medical_reasoning_node` → `unmute_node`
- `postprocess_node` (web source) → `unmute_node`
- Each call starts new background thread

## Execution Flow Example

```
1. User: "What's the weather today?"
2. llm_tagger_node: Returns "web" tag
3. Parallel execution starts:
   ├── unmute_node: Starts streaming "WEB" to Unmute
   └── processing_router: Routes to web_node
4. web_node: Performs web search
5. postprocess_node: Processes results
6. postprocess_node: Routes to unmute_node (web source)
7. unmute_node: Starts streaming final answer to Unmute
8. Both branches complete independently
```

## Benefits

- ✅ **Non-blocking**: Unmute streaming doesn't delay main workflow
- ✅ **Real-time**: Frontend receives chunks immediately  
- ✅ **Scalable**: Multiple unmute calls possible
- ✅ **Clean**: Side-effects isolated from main logic
- ✅ **LangGraph Native**: Uses built-in parallel execution 