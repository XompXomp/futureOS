# 2024-07-20: Stateless API Design

## Overview
Refactored the agent and backend API to enable fully stateless communication between frontend and backend. All state (patientProfile, conversation, memory) is now passed as JSON, with no file I/O.

## Key Changes
- **/api/agent Endpoint**: Now accepts and returns all state as JSON, supporting stateless frontend-backend communication.
- **In-Memory Data Handling**: All patient profile, memory, and conversation operations are performed in-memory using dicts.
- **Refactored patient_tools and Workflow**:
  - `read_patient_profile` and `update_patient_profile` now operate on `state['patientProfile']` (dict), not files.
  - `EnhancedSupervisorWorkflow.run` accepts and returns all state dicts, updating tool execution logic accordingly.
- **Embedding Model**: Global instantiation of SentenceTransformers (all-MiniLM-L6-v2) for semantic memory search, performed in-memory.
- **Fact-Checking Prompt**: LLM prompt for fact-checking now returns a multiline response: first line is 'yes' or 'no', second line is the reason.
- **Conversation Handling**: Conversation dict is passed and updated throughout the workflow.
- **Type Safety and Linter Fixes**: All relevant dicts use `Dict[str, Any]` or `Optional[dict]` as appropriate.
- **Error Handling**: All endpoints and workflow methods return structured dicts with error keys as needed.
- **API Endpoint Structure**: Endpoint extracts latest user message, calls agent, and returns updated state and agent response in structured JSON. 