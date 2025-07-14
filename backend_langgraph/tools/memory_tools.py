from typing import Dict, Any, List
from utils.memory_system import CurorMemorySystem
from utils.logging_config import logger

def create_memory_tools(patient_id: str = "default_patient"):
    """
    Create memory tools for the Curor Agent system.
    
    Args:
        patient_id: Patient identifier for memory isolation
        
    Returns:
        List of memory tools
    """
    memory_system = CurorMemorySystem(patient_id)
    
    def update_semantic_memory_tool(state: Dict[str, Any]) -> Dict[str, Any]:
        """Tool to update semantic memory with new information."""
        try:
            content = state.get("content", "")
            category = state.get("category", "general")
            metadata = state.get("metadata", {})
            
            if not content:
                return {
                    "error": "Content is required for semantic memory update",
                    "valid_fields": ["content", "category", "metadata"]
                }
            
            memory_id = memory_system.update_semantic_memory(content, category, metadata)
            
            if memory_id:
                return {
                    "status": "success",
                    "action": "semantic_memory_updated",
                    "memory_id": memory_id,
                    "content": content,
                    "category": category,
                    "patient_id": patient_id
                }
            else:
                return {
                    "error": "Failed to update semantic memory",
                    "content": content,
                    "category": category
                }
                
        except Exception as e:
            logger.error(f"Error in update_semantic_memory_tool: {e}")
            return {
                "error": f"Semantic memory update failed: {str(e)}",
                "content": state.get("content", ""),
                "category": state.get("category", "")
            }
    
    def search_semantic_memory_tool(state: Dict[str, Any]) -> Dict[str, Any]:
        """Tool to search semantic memory."""
        try:
            query = state.get("query", "")
            category = state.get("category")
            limit = state.get("limit", 5)
            
            if not query:
                return {
                    "error": "Query is required for semantic memory search",
                    "valid_fields": ["query", "category", "limit"]
                }
            
            results = memory_system.search_semantic_memory(query, category, limit)
            
            return {
                "status": "success",
                "action": "semantic_memory_search",
                "query": query,
                "category": category,
                "results_count": len(results),
                "results": results,
                "patient_id": patient_id
            }
            
        except Exception as e:
            logger.error(f"Error in search_semantic_memory_tool: {e}")
            return {
                "error": f"Semantic memory search failed: {str(e)}",
                "query": state.get("query", "")
            }
    
    def store_episodic_memory_tool(state: Dict[str, Any]) -> Dict[str, Any]:
        """Tool to store episodic memory."""
        try:
            interaction_type = state.get("interaction_type", "")
            content = state.get("content", "")
            reasoning_context = state.get("reasoning_context", "")
            outcome = state.get("outcome", "")
            metadata = state.get("metadata", {})
            
            if not all([interaction_type, content, reasoning_context, outcome]):
                return {
                    "error": "All fields are required for episodic memory storage",
                    "valid_fields": ["interaction_type", "content", "reasoning_context", "outcome", "metadata"]
                }
            
            episode_id = memory_system.store_episodic_memory(
                interaction_type, content, reasoning_context, outcome, metadata
            )
            
            if episode_id:
                return {
                    "status": "success",
                    "action": "episodic_memory_stored",
                    "episode_id": episode_id,
                    "interaction_type": interaction_type,
                    "patient_id": patient_id
                }
            else:
                return {
                    "error": "Failed to store episodic memory",
                    "interaction_type": interaction_type
                }
                
        except Exception as e:
            logger.error(f"Error in store_episodic_memory_tool: {e}")
            return {
                "error": f"Episodic memory storage failed: {str(e)}",
                "interaction_type": state.get("interaction_type", "")
            }
    
    def search_episodic_memory_tool(state: Dict[str, Any]) -> Dict[str, Any]:
        """Tool to search episodic memory."""
        try:
            interaction_type = state.get("interaction_type")
            limit = state.get("limit", 10)
            
            results = memory_system.search_episodic_memory(interaction_type, limit)
            
            return {
                "status": "success",
                "action": "episodic_memory_search",
                "interaction_type": interaction_type,
                "results_count": len(results),
                "results": results,
                "patient_id": patient_id
            }
            
        except Exception as e:
            logger.error(f"Error in search_episodic_memory_tool: {e}")
            return {
                "error": f"Episodic memory search failed: {str(e)}",
                "interaction_type": state.get("interaction_type")
            }
    
    def update_procedural_memory_tool(state: Dict[str, Any]) -> Dict[str, Any]:
        """Tool to update procedural memory."""
        try:
            rule_type = state.get("rule_type", "")
            rule_data = state.get("rule_data", {})
            
            if not rule_type or not rule_data:
                return {
                    "error": "Rule type and rule data are required for procedural memory update",
                    "valid_fields": ["rule_type", "rule_data"]
                }
            
            memory_system.update_procedural_memory(rule_type, rule_data)
            
            return {
                "status": "success",
                "action": "procedural_memory_updated",
                "rule_type": rule_type,
                "rule_data": rule_data,
                "patient_id": patient_id
            }
            
        except Exception as e:
            logger.error(f"Error in update_procedural_memory_tool: {e}")
            return {
                "error": f"Procedural memory update failed: {str(e)}",
                "rule_type": state.get("rule_type", "")
            }
    
    def get_procedural_memory_tool(state: Dict[str, Any]) -> Dict[str, Any]:
        """Tool to get procedural memory."""
        try:
            rule_type = state.get("rule_type")
            
            rules = memory_system.get_procedural_memory(rule_type)
            
            return {
                "status": "success",
                "action": "procedural_memory_retrieved",
                "rule_type": rule_type,
                "rules": rules,
                "patient_id": patient_id
            }
            
        except Exception as e:
            logger.error(f"Error in get_procedural_memory_tool: {e}")
            return {
                "error": f"Procedural memory retrieval failed: {str(e)}",
                "rule_type": state.get("rule_type")
            }
    
    def optimize_prompt_tool(state: Dict[str, Any]) -> Dict[str, Any]:
        """Tool to optimize prompts using procedural memory."""
        try:
            base_prompt = state.get("base_prompt", "")
            context = state.get("context", {})
            
            if not base_prompt:
                return {
                    "error": "Base prompt is required for optimization",
                    "valid_fields": ["base_prompt", "context"]
                }
            
            optimized_prompt = memory_system.optimize_prompt(base_prompt, context)
            
            return {
                "status": "success",
                "action": "prompt_optimized",
                "base_prompt": base_prompt,
                "optimized_prompt": optimized_prompt,
                "context": context,
                "patient_id": patient_id
            }
            
        except Exception as e:
            logger.error(f"Error in optimize_prompt_tool: {e}")
            return {
                "error": f"Prompt optimization failed: {str(e)}",
                "base_prompt": state.get("base_prompt", "")
            }
    
    def get_memory_summary_tool(state: Dict[str, Any]) -> Dict[str, Any]:
        """Tool to get a comprehensive memory summary."""
        try:
            summary = memory_system.get_memory_summary()
            
            return {
                "status": "success",
                "action": "memory_summary_retrieved",
                "summary": summary,
                "patient_id": patient_id
            }
            
        except Exception as e:
            logger.error(f"Error in get_memory_summary_tool: {e}")
            return {
                "error": f"Memory summary retrieval failed: {str(e)}"
            }
    
    # Set function names for tools
    update_semantic_memory_tool.__name__ = "update_semantic_memory"
    search_semantic_memory_tool.__name__ = "search_semantic_memory"
    store_episodic_memory_tool.__name__ = "store_episodic_memory"
    search_episodic_memory_tool.__name__ = "search_episodic_memory"
    update_procedural_memory_tool.__name__ = "update_procedural_memory"
    get_procedural_memory_tool.__name__ = "get_procedural_memory"
    optimize_prompt_tool.__name__ = "optimize_prompt"
    get_memory_summary_tool.__name__ = "get_memory_summary"
    
    return [
        update_semantic_memory_tool,
        search_semantic_memory_tool,
        store_episodic_memory_tool,
        search_episodic_memory_tool,
        update_procedural_memory_tool,
        get_procedural_memory_tool,
        optimize_prompt_tool,
        get_memory_summary_tool
    ] 