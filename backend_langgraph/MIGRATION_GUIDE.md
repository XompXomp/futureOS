# MIGRATION GUIDE: Multi-Agent LLM-Driven LangGraph Backend

## Overview

This guide describes the migration to a fully LLM-driven, multi-agent backend using LangGraph, with advanced memory (procedural, episodic, semantic) and prompt optimization for each agent. All routing and tool selection is now LLM-driven, and all agents use vector semantic search for memory and context.

---

## Directory Structure (Key Files Only)

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
└── MIGRATION_GUIDE.md            # This migration guide
```

---

## Key Migration Steps

1. **Remove all keyword-based routing and legacy nodes.**
2. **Implement LLM-driven ReAct agents for each domain (patient, file, web, text).**
3. **Add advanced memory for each agent:**
   - Procedural, episodic, and semantic memory (vector search)
   - Prompt optimizer for each agent
4. **Restore and update all tools to use semantic extraction (not regex/keywords).**
5. **Orchestrator agent now uses LLM-driven routing and has its own advanced memory.**
6. **All agents and tools are registered in the workflow graph.**
7. **All state and context is passed through the workflow and agents.**

---

## How to Migrate Your Code

- **Agents:**
  - Use `create_react_agent` with memory tools, prompt optimizer, and checkpointer.
  - Register all relevant tools for each agent.
  - Use separate namespaces for profile, episodic, and procedural memory.

- **Tools:**
  - Implement all tools as pure functions that operate on the workflow state.
  - Use semantic extraction for all user input parsing.

- **Workflow:**
  - The workflow graph should only have an entry node and an agent executor node.
  - All routing and tool selection is handled by the orchestrator agent.

- **State:**
  - Use a unified state schema for all agents and tools.

---

## Notes
- All memory is embedding-based (vector search, not keyword).
- All tool selection and routing is LLM-driven (no hardcoded rules).
- Each agent is fully modular and can be extended with new tools or memory types.
- Prompt optimization is used for all LLM calls.

---

For more details, see the updated `README.md`. 