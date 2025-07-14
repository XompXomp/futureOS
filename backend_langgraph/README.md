# LangGraph Multi-Agent Backend

## Overview

This backend implements a fully LLM-driven, multi-agent architecture using LangGraph. Each agent (Patient, File, Web, Text, Orchestrator) uses advanced memory (procedural, episodic, semantic) and prompt optimization. All routing and tool selection is LLM-driven, and all agents use vector semantic search for memory and context.

---

## Directory Structure (Key Files)

```
backend_langgraph/
├── agents/
│   ├── orchestrator_agent.py      # LLM-driven router, advanced memory, routes to specialized agents
│   ├── patient_agent.py          # Patient profile agent (ReAct, advanced memory)
│   ├── file_agent.py             # File operations agent (ReAct, advanced memory)
│   ├── web_agent.py              # Web search agent (ReAct, advanced memory)
│   └── text_agent.py             # Text processing agent (ReAct, advanced memory)
├── tools/
│   ├── patient_tools.py          # Patient profile read/update tools (semantic extraction)
│   ├── file_tools.py             # File read/write tools (semantic extraction)
│   ├── web_search_tools.py       # Web search/weather tools (semantic extraction)
│   └── text_tools.py             # Summarization, database, keyword tools (semantic extraction)
├── graph/
│   └── multi_agent_graph.py      # Defines the workflow graph (entry, agent executor)
├── nodes/
│   └── input_processor.py        # Preprocesses user input, manages state
├── state/
│   └── schema.py                 # State schema for workflow
├── config/
│   └── settings.py               # Configuration (paths, constants)
├── utils/
│   └── logging_config.py         # Logging setup
├── data/
│   └── docs/
│       └── patient_profile.json  # Example patient profile data
├── main.py                       # Main entry point (CLI chat loop)
├── requirements.txt              # Python dependencies
├── README.md                     # Project overview and usage
└── MIGRATION_GUIDE.md            # Migration guide
```

---

## Agent Design

- **OrchestratorAgent**: LLM-driven router, advanced memory, routes to specialized agents
- **PatientAgent**: Handles patient profile tasks, uses procedural, episodic, and semantic memory
- **FileAgent**: Handles file operations, uses procedural, episodic, and semantic memory
- **WebAgent**: Handles web search, uses procedural, episodic, and semantic memory
- **TextAgent**: Handles text processing, uses procedural, episodic, and semantic memory

All agents use:
- **ReAct pattern** for LLM-driven reasoning and tool selection
- **Prompt optimization** for better LLM performance
- **Vector semantic search** for memory/context retrieval

---

## Memory Types

- **Procedural Memory**: Stores workflows, procedures, and how-tos
- **Episodic Memory**: Stores past experiences, conversations, and events
- **Semantic Memory**: Stores domain-specific knowledge and facts
- **Prompt Optimization**: Improves LLM prompt quality for each agent

Each agent has its own memory namespaces for these types.

---

## How to Run

1. **Install dependencies:**
   ```bash
   pip install -r backend_langgraph/requirements.txt
   ```
2. **Configure settings:**
   - Edit `backend_langgraph/config/settings.py` for paths, LLM keys, etc.
3. **Run the main app:**
   ```bash
   python backend_langgraph/main.py
   ```
4. **Interact via CLI:**
   - Type your queries and the orchestrator will route them to the appropriate agent.

---

## Extending the System

- **Add new tools:** Implement a new function in the appropriate `tools/` file and register it with the relevant agent.
- **Add new agents:** Create a new agent class in `agents/`, add memory tools, and register it in the orchestrator.
- **Customize memory:** Adjust namespaces or add new memory types as needed.

---

## Key Features

- LLM-driven multi-agent orchestration
- Advanced memory (procedural, episodic, semantic) for each agent
- Prompt optimization for all LLM calls
- Vector semantic search for memory/context
- Modular, extensible, and fully state-driven

---

For migration details, see `MIGRATION_GUIDE.md`. 