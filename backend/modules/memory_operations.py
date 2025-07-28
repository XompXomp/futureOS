import uuid
from config.settings import settings
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime

embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

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
            memory_datetime = datetime.now().replace(microsecond=0).isoformat()
            new_entry = {
                "id": memory_id,
                "datetime": memory_datetime,
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
            if not semantic_list:
                state['results'] = []
                return state

            # Filter by category if provided
            filtered_memories = [
                m for m in semantic_list 
                if not category or m.get("category") == category
            ]

            if not filtered_memories:
                state['results'] = []
                return state

            # Compute embeddings only temporarily (not stored)
            memory_embeddings = embedding_model.encode(
                [m["content"] for m in filtered_memories],
                convert_to_numpy=True
            )
            query_embedding = embedding_model.encode(query, convert_to_numpy=True)

            scores = cosine_similarity([query_embedding], memory_embeddings)[0]
            top_indices = scores.argsort()[::-1][:limit]

            # Optional: include similarity score in results if you want
            results = [filtered_memories[i] for i in top_indices]

            state['results'] = results
            return state
        except Exception as e:
            state['error'] = f"Semantic memory search failed: {str(e)}"
            return state