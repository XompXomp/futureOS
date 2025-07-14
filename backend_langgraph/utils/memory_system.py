import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import yaml
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

class CurorMemorySystem:
    """
    Comprehensive memory system for Curor Agent with semantic, episodic, and procedural memory.
    """
    
    def __init__(self, patient_id: str, base_path: str = "data/memory"):
        self.patient_id = patient_id
        self.base_path = Path(base_path)
        self.patient_memory_path = self.base_path / patient_id
        
        # Create directory structure
        self.semantic_path = self.patient_memory_path / "semantic_memory_store"
        self.episodes_path = self.patient_memory_path / "episodes"
        self.procedural_path = self.patient_memory_path / "procedural"
        
        # Ensure directories exist
        for path in [self.semantic_path, self.episodes_path, self.procedural_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding model for semantic search
        try:
            self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        except Exception as e:
            logger.warning(f"Could not load embedding model: {e}")
            self.embedding_model = None
        
        # Load patient profile
        self.patient_profile_path = Path("data/docs/patient_profile.json")
        self.patient_profile = self._load_patient_profile()
        
        # Initialize procedural memory
        self.prompt_rules_path = self.procedural_path / "prompt_rules.yaml"
        self.prompt_rules = self._load_prompt_rules()
    
    def _load_patient_profile(self) -> Dict[str, Any]:
        """Load patient profile from JSON file."""
        try:
            if self.patient_profile_path.exists():
                with open(self.patient_profile_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Patient profile not found at {self.patient_profile_path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading patient profile: {e}")
            return {}
    
    def _load_prompt_rules(self) -> Dict[str, Any]:
        """Load procedural memory rules from YAML file."""
        try:
            if self.prompt_rules_path.exists():
                with open(self.prompt_rules_path, 'r') as f:
                    return yaml.safe_load(f)
            else:
                # Initialize default prompt rules
                default_rules = {
                    "communication_style": {
                        "tone": "professional_empathetic",
                        "preferred_analogies": True,
                        "technical_level": "moderate",
                        "response_length": "detailed"
                    },
                    "interaction_patterns": {
                        "follow_up_frequency": "weekly",
                        "preferred_contact_method": "text",
                        "appointment_preferences": "morning"
                    },
                    "medical_preferences": {
                        "treatment_approach": "conservative",
                        "information_sharing": "detailed",
                        "family_involvement": True
                    }
                }
                self._save_prompt_rules(default_rules)
                return default_rules
        except Exception as e:
            logger.error(f"Error loading prompt rules: {e}")
            return {}
    
    def _save_prompt_rules(self, rules: Dict[str, Any]):
        """Save procedural memory rules to YAML file."""
        try:
            with open(self.prompt_rules_path, 'w') as f:
                yaml.dump(rules, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error saving prompt rules: {e}")
    
    def update_semantic_memory(self, content: str, category: str = "general", 
                              metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Update semantic memory with new information.
        
        Args:
            content: The information to store
            category: Category of information (e.g., 'medical_condition', 'preference')
            metadata: Additional metadata for the memory
            
        Returns:
            Memory ID
        """
        memory_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Create memory entry
        memory_entry = {
            "id": memory_id,
            "content": content,
            "category": category,
            "timestamp": timestamp,
            "metadata": metadata or {},
            "patient_id": self.patient_id
        }
        
        # Save to semantic memory store
        memory_file = self.semantic_path / f"{memory_id}.json"
        try:
            with open(memory_file, 'w') as f:
                json.dump(memory_entry, f, indent=2)
            
            # Update patient profile if it's profile-related information
            if category in ["preference", "medical_condition", "medication", "allergy"]:
                self._update_patient_profile(content, category, metadata)
            
            logger.info(f"Semantic memory updated: {memory_id}")
            return memory_id
        except Exception as e:
            logger.error(f"Error updating semantic memory: {e}")
            return ""
    
    def _update_patient_profile(self, content: str, category: str, metadata: Dict[str, Any]):
        """Update patient profile with new information."""
        try:
            if category == "preference":
                if "preferred_doctor" in content.lower():
                    self.patient_profile.setdefault("preferences", {})["preferred_doctor"] = content
                elif "appointment_time" in content.lower():
                    self.patient_profile.setdefault("preferences", {})["appointment_time"] = content
            
            elif category == "medical_condition":
                conditions = self.patient_profile.get("medical_info", {}).get("chronic_conditions", [])
                if content not in conditions:
                    conditions.append(content)
                    self.patient_profile.setdefault("medical_info", {})["chronic_conditions"] = conditions
            
            elif category == "medication":
                medications = self.patient_profile.get("medical_info", {}).get("current_medications", [])
                if content not in medications:
                    medications.append(content)
                    self.patient_profile.setdefault("medical_info", {})["current_medications"] = medications
            
            elif category == "allergy":
                allergies = self.patient_profile.get("medical_info", {}).get("allergies", [])
                if content not in allergies:
                    allergies.append(content)
                    self.patient_profile.setdefault("medical_info", {})["allergies"] = allergies
            
            # Save updated profile
            with open(self.patient_profile_path, 'w') as f:
                json.dump(self.patient_profile, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating patient profile: {e}")
    
    def search_semantic_memory(self, query: str, category: Optional[str] = None, 
                              limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search semantic memory using vector similarity.
        
        Args:
            query: Search query
            category: Filter by category
            limit: Maximum number of results
            
        Returns:
            List of relevant memory entries
        """
        if not self.embedding_model:
            return self._fallback_semantic_search(query, category, limit)
        
        try:
            # Get query embedding
            query_embedding = self.embedding_model.encode([query])[0]
            
            # Load all semantic memories
            memories = []
            for memory_file in self.semantic_path.glob("*.json"):
                try:
                    with open(memory_file, 'r') as f:
                        memory = json.load(f)
                    
                    # Filter by category if specified
                    if category and memory.get("category") != category:
                        continue
                    
                    memories.append(memory)
                except Exception as e:
                    logger.warning(f"Error reading memory file {memory_file}: {e}")
            
            if not memories:
                return []
            
            # Calculate similarities
            similarities = []
            for memory in memories:
                try:
                    memory_embedding = self.embedding_model.encode([memory["content"]])[0]
                    similarity = cosine_similarity([query_embedding], [memory_embedding])[0][0]
                    similarities.append((similarity, memory))
                except Exception as e:
                    logger.warning(f"Error calculating similarity for memory {memory.get('id')}: {e}")
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[0], reverse=True)
            return [memory for _, memory in similarities[:limit]]
            
        except Exception as e:
            logger.error(f"Error in semantic memory search: {e}")
            return self._fallback_semantic_search(query, category, limit)
    
    def _fallback_semantic_search(self, query: str, category: Optional[str] = None, 
                                 limit: int = 5) -> List[Dict[str, Any]]:
        """Fallback search when embedding model is not available."""
        try:
            memories = []
            for memory_file in self.semantic_path.glob("*.json"):
                try:
                    with open(memory_file, 'r') as f:
                        memory = json.load(f)
                    
                    # Filter by category if specified
                    if category and memory.get("category") != category:
                        continue
                    
                    # Simple keyword matching
                    if query.lower() in memory["content"].lower():
                        memories.append(memory)
                        
                except Exception as e:
                    logger.warning(f"Error reading memory file {memory_file}: {e}")
            
            return memories[:limit]
        except Exception as e:
            logger.error(f"Error in fallback semantic search: {e}")
            return []
    
    def store_episodic_memory(self, interaction_type: str, content: str, 
                              reasoning_context: str, outcome: str,
                              metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store episodic memory of successful interactions.
        
        Args:
            interaction_type: Type of interaction (e.g., 'triage', 'symptom_mapping')
            content: The interaction content
            reasoning_context: Context and reasoning used
            outcome: Outcome of the interaction
            metadata: Additional metadata
            
        Returns:
            Episode ID
        """
        episode_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        episode = {
            "id": episode_id,
            "interaction_type": interaction_type,
            "content": content,
            "reasoning_context": reasoning_context,
            "outcome": outcome,
            "timestamp": timestamp,
            "metadata": metadata or {},
            "patient_id": self.patient_id
        }
        
        # Save episode
        episode_file = self.episodes_path / f"{episode_id}.json"
        try:
            with open(episode_file, 'w') as f:
                json.dump(episode, f, indent=2)
            
            logger.info(f"Episodic memory stored: {episode_id}")
            return episode_id
        except Exception as e:
            logger.error(f"Error storing episodic memory: {e}")
            return ""
    
    def search_episodic_memory(self, interaction_type: Optional[str] = None, 
                              limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search episodic memory for relevant past interactions.
        
        Args:
            interaction_type: Filter by interaction type
            limit: Maximum number of results
            
        Returns:
            List of relevant episodes
        """
        try:
            episodes = []
            for episode_file in self.episodes_path.glob("*.json"):
                try:
                    with open(episode_file, 'r') as f:
                        episode = json.load(f)
                    
                    # Filter by interaction type if specified
                    if interaction_type and episode.get("interaction_type") != interaction_type:
                        continue
                    
                    episodes.append(episode)
                except Exception as e:
                    logger.warning(f"Error reading episode file {episode_file}: {e}")
            
            # Sort by timestamp (most recent first)
            episodes.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return episodes[:limit]
            
        except Exception as e:
            logger.error(f"Error searching episodic memory: {e}")
            return []
    
    def update_procedural_memory(self, rule_type: str, rule_data: Dict[str, Any]):
        """
        Update procedural memory with new behavior rules.
        
        Args:
            rule_type: Type of rule (e.g., 'communication_style', 'interaction_patterns')
            rule_data: The rule data to update
        """
        try:
            if rule_type not in self.prompt_rules:
                self.prompt_rules[rule_type] = {}
            
            self.prompt_rules[rule_type].update(rule_data)
            self._save_prompt_rules(self.prompt_rules)
            
            logger.info(f"Procedural memory updated: {rule_type}")
        except Exception as e:
            logger.error(f"Error updating procedural memory: {e}")
    
    def get_procedural_memory(self, rule_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get procedural memory rules.
        
        Args:
            rule_type: Specific rule type to retrieve
            
        Returns:
            Procedural memory rules
        """
        if rule_type:
            return self.prompt_rules.get(rule_type, {})
        return self.prompt_rules
    
    def optimize_prompt(self, base_prompt: str, context: Dict[str, Any] = None) -> str:
        """
        Optimize prompt using procedural memory and context.
        
        Args:
            base_prompt: The base prompt to optimize
            context: Additional context for optimization
            
        Returns:
            Optimized prompt
        """
        try:
            # Get relevant procedural rules
            communication_style = self.prompt_rules.get("communication_style", {})
            interaction_patterns = self.prompt_rules.get("interaction_patterns", {})
            medical_preferences = self.prompt_rules.get("medical_preferences", {})
            
            # Build optimization instructions
            optimization_instructions = []
            
            if communication_style.get("tone") == "professional_empathetic":
                optimization_instructions.append("Maintain a professional yet empathetic tone")
            
            if communication_style.get("preferred_analogies"):
                optimization_instructions.append("Use analogies and metaphors when explaining complex medical concepts")
            
            if communication_style.get("technical_level") == "moderate":
                optimization_instructions.append("Use moderate technical language - explain medical terms when used")
            
            if medical_preferences.get("treatment_approach") == "conservative":
                optimization_instructions.append("Prefer conservative treatment approaches when multiple options exist")
            
            if medical_preferences.get("information_sharing") == "detailed":
                optimization_instructions.append("Provide detailed explanations and information")
            
            # Apply optimizations
            optimized_prompt = base_prompt
            
            if optimization_instructions:
                optimization_text = "\n".join([f"- {instruction}" for instruction in optimization_instructions])
                optimized_prompt += f"\n\nOptimization Instructions:\n{optimization_text}"
            
            # Add context if provided
            if context:
                context_text = "\n".join([f"{key}: {value}" for key, value in context.items()])
                optimized_prompt += f"\n\nContext:\n{context_text}"
            
            return optimized_prompt
            
        except Exception as e:
            logger.error(f"Error optimizing prompt: {e}")
            return base_prompt
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all memory types for the patient.
        
        Returns:
            Memory summary
        """
        try:
            # Count semantic memories
            semantic_count = len(list(self.semantic_path.glob("*.json")))
            
            # Count episodes
            episode_count = len(list(self.episodes_path.glob("*.json")))
            
            # Get recent episodes
            recent_episodes = self.search_episodic_memory(limit=3)
            
            # Get patient profile summary
            profile_summary = {
                "name": self.patient_profile.get("personal_info", {}).get("name", "Unknown"),
                "age": self.patient_profile.get("personal_info", {}).get("age", "Unknown"),
                "chronic_conditions": self.patient_profile.get("medical_info", {}).get("chronic_conditions", []),
                "medications": self.patient_profile.get("medical_info", {}).get("current_medications", []),
                "allergies": self.patient_profile.get("medical_info", {}).get("allergies", [])
            }
            
            return {
                "patient_id": self.patient_id,
                "semantic_memory_count": semantic_count,
                "episodic_memory_count": episode_count,
                "procedural_rules": list(self.prompt_rules.keys()),
                "recent_episodes": recent_episodes,
                "profile_summary": profile_summary
            }
            
        except Exception as e:
            logger.error(f"Error getting memory summary: {e}")
            return {"error": str(e)} 