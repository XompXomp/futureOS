import uuid
from config.settings import settings

class MemoryOperations:
    @staticmethod
    def update_semantic_memory(state: dict) -> dict:
        try:
            content = state.get("content", "")
            category = state.get("category", "general")
            metadata = state.get("metadata", {})
            memory = state.get("memory") or {}
            if not content:
                state['error'] = "Content is required for semantic memory update"
                return state
            semantic_list = memory.setdefault("semantic", [])
            memory_id = str(uuid.uuid4())
            new_entry = {
                "id": memory_id,
                "content": content,
                "category": category,
                "metadata": metadata,
                "patient_id": state.get("patient_id", "default_patient")
            }
            semantic_list.append(new_entry)
            state['memory'] = memory
            return state
        except Exception as e:
            state['error'] = f"Semantic memory update failed: {str(e)}"
            return state

    @staticmethod
    def search_semantic_memory(state: dict) -> dict:
        try:
            query = state.get("query", "")
            category = state.get("category")
            limit = state.get("limit", 5)
            memory = state.get("memory") or {}
            if not query:
                state['error'] = "Query is required for semantic memory search"
                return state
            semantic_list = memory.get("semantic", [])
            results = [m for m in semantic_list if (not category or m.get("category") == category) and query.lower() in m.get("content", "").lower()][:limit]
            state['results'] = results
            return state
        except Exception as e:
            state['error'] = f"Semantic memory search failed: {str(e)}"
            return state