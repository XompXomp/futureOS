# LangGraph Backend

A patient management AI backend built with LangGraph and LangMem for advanced stateful workflows and memory management.

## Features

- **LangGraph Workflows**: Stateful, directed graph-based workflows
- **LangMem Integration**: Semantic and episodic memory for context retention
- **Modular Tools**: Patient profile management, file operations, web search, text processing
- **LLM Integration**: Support for Groq and Ollama models
- **Error Handling**: Robust error handling and logging

## Structure

```
backend_langgraph/
├── config/           # Configuration settings
├── graph/           # LangGraph workflow definitions
├── nodes/           # Graph nodes (input processing, routing, response generation)
├── state/           # State schema definitions
├── tools/           # Tool implementations as graph nodes
├── utils/           # Utilities (logging, etc.)
├── main.py          # Main entry point
└── requirements.txt # Dependencies
```

## Key Components

### State Management
- `PatientState`: TypedDict defining the workflow state
- Includes conversation history, patient profile, tool results, and memory

### Graph Nodes
- **Input Processor**: Processes user input and initializes state
- **Memory Retriever**: Retrieves relevant context from LangMem
- **LLM Router**: Routes to appropriate tools based on user input
- **Response Generator**: Creates final responses using LLM

### Tools (as Graph Nodes)
- **Patient Tools**: Read/update patient profiles
- **File Tools**: Read/write files
- **Web Search**: Google PSE integration
- **Text Tools**: Summarization and database queries

### Memory System
- **Semantic Memory**: Stores and retrieves semantic information
- **Episodic Memory**: Stores conversation history and events
- **Configurable**: Similarity thresholds and retrieval parameters

## Usage

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
# .env file
OPENAI_API_KEY=your_key
GOOGLE_PSE_API_KEY=your_key
GOOGLE_PSE_CX=your_cx
```

3. Run the agent:
```bash
python main.py
```

## Migration from LangChain

This backend represents a migration from the original LangChain implementation:

### Key Differences
- **Stateful Workflows**: LangGraph provides explicit state management
- **Advanced Memory**: LangMem offers semantic and episodic memory
- **Modular Design**: Tools are implemented as graph nodes
- **Better Control Flow**: Conditional routing and explicit state transitions

### Benefits
- **Better Memory**: Semantic search and episodic recall
- **Stateful Operations**: Maintains context across interactions
- **Explicit Workflows**: Clear data flow and decision points
- **Scalability**: Easier to extend and modify workflows

## Configuration

Key settings in `config/settings.py`:
- Memory retrieval parameters
- LLM model selection
- Tool routing thresholds
- Error handling settings

## Development

The modular structure makes it easy to:
- Add new tools as graph nodes
- Modify routing logic
- Extend memory capabilities
- Customize state schema 