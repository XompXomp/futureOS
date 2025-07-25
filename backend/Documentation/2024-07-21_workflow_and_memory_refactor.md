# 2024-07-21: Workflow and Memory Refactor

## Overview
Major refactor to support stateless, in-memory operations for patient profile, conversation, and memory. Enhanced workflow and tool logic for improved reliability and API compatibility.

## Key Changes
- Stateless API design: `/api/agent` endpoint now fully stateless, passing all state as JSON.
- In-memory data handling: All operations on patient profile, memory, and conversation are performed in-memory.
- Refactored patient_tools and workflow to operate on state dicts.
- Embedding model for semantic memory search is globally instantiated and used in-memory.
- Fact-checking prompt returns multiline response (yes/no + reason).
- Conversation dict is updated throughout the workflow.
- Type safety: All dicts use `Dict[str, Any]` or `Optional[dict]`.
- Error handling: Structured dicts with error keys.
- API endpoint structure: Extracts latest user message, calls agent, returns updated state and response as JSON. 