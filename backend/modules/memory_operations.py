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
            text = state.get("input", "")
            memory = state.get("memory") or []
            if not text:
                state['error'] = "Text is required for semantic memory update"
                return state
            memory_datetime = datetime.now().strftime("%d_%m_%y_%H_%M")
            new_entry = {
                "text": text,
                "datetime": memory_datetime
                
            }
            memory.append(new_entry)
            state['memory'] = memory
            return state
        except Exception as e:
            state['error'] = f"Semantic memory update failed: {str(e)}"
            return state

    @staticmethod
    def search_semantic_memory(state: dict) -> dict:
        try:
            query = state.get("query", "")
            limit = state.get("limit", 5)
            memory = state.get("memory") or []

            if not query:
                state['error'] = "Query is required for semantic memory search"
                return state

            if not memory:
                state['results'] = []
                return state

            # Compute embeddings for all memory entries
            memory_texts = [m["text"] for m in memory]
            memory_embeddings = embedding_model.encode(
                memory_texts,
                convert_to_numpy=True
            )
            query_embedding = embedding_model.encode(query, convert_to_numpy=True)

            scores = cosine_similarity([query_embedding], memory_embeddings)[0]
            top_indices = scores.argsort()[::-1][:limit]

            # Return top results with their original structure
            results = [memory[i] for i in top_indices]

            state['results'] = results
            return state
        except Exception as e:
            state['error'] = f"Semantic memory search failed: {str(e)}"
            return state