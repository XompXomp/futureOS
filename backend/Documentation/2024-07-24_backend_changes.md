# 2024-07-24: Backend Changes

## Overview
This log summarizes all backend changes and improvements made on 2024-07-24, continuing the stateless, in-memory architecture and enhancing reliability, maintainability, and API compatibility.

## Key Changes
- Further refactored agent and workflow logic for improved modularity and maintainability.
- Enhanced error handling and validation across all endpoints and workflow nodes.
- Optimized semantic memory search and storage for better performance and deduplication.
- Improved LLM prompt engineering for more accurate tool selection and fact-checking.
- Refined patient profile and memory data structures for consistency between frontend and backend.
- Added/updated documentation and diagrams to reflect the latest workflow and architecture.
- Fixed bugs related to state mutation and response formatting in the API.
- Improved type safety and linter compliance throughout the backend codebase.

## Outcome
The backend is now more robust, maintainable, and production-ready, with improved memory management, API integration, and workflow reliability.

## Artifacts
- Updated workflow diagram: `Updated_workflow.png`
- Documentation logs for previous days: see `2024-07-20_stateless_api_design.md`, `2024-07-21_workflow_and_memory_refactor.md`, `2024-07-22_backend_ai_agent_enhancements.md`. 

---

## Specific New Architecture Implemented on 2024-07-24

### 1. Modular, Node-Based Workflow with LangGraph
- The backend now uses a node-based workflow orchestration (via `LangGraph`) where each node represents a distinct operation or decision point:
  - **llm_tagger_node**: Uses an LLM to tag/reroute the request (e.g., text, patient, web, medical, UI change).
  - **semantic_memory_precheck_node**: Checks if the input is about the patient profile or should trigger a semantic memory search/update.
  - **text_node, patient_node, web_node, medical_reasoning_node, semantic_update_node, ui_change_node**: Each handles a specific type of request or tool execution.
  - **postprocess_node**: Finalizes the response, formatting it for the API.

### 2. Dynamic Conditional Routing
- Conditional edges in the workflow allow dynamic routing based on the current state and LLM decisions.
- The workflow can branch to different nodes (e.g., semantic memory, patient, web, UI) depending on the `route_tag` and other state variables.
- This enables flexible, extensible agent behavior and easy addition of new capabilities.

### 3. Unified, Typed State Management
- All agent state is managed in a single `AgentState` TypedDict, which is passed and mutated through every node.
- This state includes: user input, memory, patient profile, final answer, error, insights, updates, and routing tags.
- No file I/O: All state is in-memory and passed as JSON between frontend and backend.

### 4. Semantic Memory Precheck and Update
- Before routing to a tool, the system:
  - Checks if the input is about the patient profile (using LLM).
  - Performs a semantic search for relevant memories (using vector embeddings).
  - Uses an LLM to decide if new information should be stored in semantic memory, preventing duplicates and irrelevant data.

### 5. Tool Selection via LLM
- Tool selection for patient and web operations is performed by an LLM, using tool metadata and user input.
- This allows for more robust, context-aware tool invocation.

### 6. UI Change Node
- A new `ui_change_node` was added to the workflow, allowing the backend to signal the frontend to perform special UI actions (e.g., show modals, update views) via the API response.

### 7. Improved Error Handling and Postprocessing
- All errors are captured in the state and returned in the API response.
- The postprocessing node ensures that the final answer is user-friendly and source-aware.

### 8. Extensibility
- The architecture is now highly extensible:
  - New tools or nodes can be added with minimal changes.
  - Routing logic is centralized and easy to update.

**Diagram Reference:**
See `Updated_workflow.png` in the documentation folder for a visual representation of the new workflow. 