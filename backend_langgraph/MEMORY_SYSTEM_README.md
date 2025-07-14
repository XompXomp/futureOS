# 🧠 Curor Memory System

A comprehensive memory system for the Curor Agent with semantic, episodic, and procedural memory types.

## Overview

The Curor Memory System provides three distinct types of memory to enable intelligent, context-aware interactions:

### Memory Types

| Memory Type | Role in Agent | Storage Pattern | Example |
|-------------|----------------|------------------|---------|
| **Semantic** | Stores patient demographics, medical facts, preferences, and known relationships between entities | `patient_profile.json` for updatable fields (e.g., preferred doctor, chronic conditions); plus a `semantic_memory_store/` folder using vector search for flexible recall | `"Patient has Type 2 Diabetes and prefers morning appointments"` |
| **Episodic** | Captures successful interactions like prior triaging logic, symptom mapping, or follow-up conversations; includes reasoning context and outcomes | Each episode stored as a JSON file in `episodes/` folder, organized by date or interaction type | `"Explained importance of insulin adherence using metaphor; patient responded positively"` |
| **Procedural** | Optimizes response style and behavior rules based on feedback and user traits; enables tone adaptation, instruction recall, and multi-turn consistency | `prompt_rules.yaml` + dynamic enrichment via `prompt_optimizer()` during interaction | `"Patient prefers explanations with analogies and dislikes overly technical terms"` |

## Architecture

```
data/memory/
├── {patient_id}/
│   ├── semantic_memory_store/
│   │   ├── {memory_id}.json
│   │   └── ...
│   ├── episodes/
│   │   ├── {episode_id}.json
│   │   └── ...
│   └── procedural/
│       └── prompt_rules.yaml
```

## Features

### ✨ Semantic Memory
- **Vector-based search** using sentence transformers
- **Category-based filtering** for precise retrieval
- **Automatic patient profile updates** for relevant information
- **Fallback keyword search** when embeddings unavailable

### 📚 Episodic Memory
- **Interaction tracking** with reasoning context
- **Outcome recording** for learning from past interactions
- **Metadata support** for rich context
- **Chronological organization** for temporal relevance

### ⚙️ Procedural Memory
- **Dynamic prompt optimization** based on patient preferences
- **Communication style adaptation** (tone, technical level, analogies)
- **Interaction pattern learning** (follow-up frequency, contact preferences)
- **YAML-based rule storage** for easy modification

## Usage

### Basic Usage

```python
from utils.memory_system import CurorMemorySystem

# Initialize memory system for a patient
memory_system = CurorMemorySystem("patient_123")

# Store semantic memory
memory_id = memory_system.update_semantic_memory(
    "Patient has Type 2 Diabetes",
    category="medical_condition"
)

# Search semantic memory
results = memory_system.search_semantic_memory("diabetes", limit=5)

# Store episodic memory
episode_id = memory_system.store_episodic_memory(
    interaction_type="medication_review",
    content="Reviewed metformin dosage",
    reasoning_context="Standard medication review protocol",
    outcome="Adjusted dosage and scheduled follow-up"
)

# Update procedural memory
memory_system.update_procedural_memory("communication_style", {
    "tone": "professional_empathetic",
    "preferred_analogies": True
})

# Optimize prompts
optimized_prompt = memory_system.optimize_prompt(
    "You are a medical assistant.",
    {"patient_condition": "diabetes"}
)
```

### Using Memory Tools

```python
from tools.memory_tools import create_memory_tools

# Create memory tools for an agent
memory_tools = create_memory_tools("patient_123")

# Use the tools in agent state
update_tool = memory_tools[0]  # update_semantic_memory_tool
result = update_tool({
    "content": "Patient is allergic to penicillin",
    "category": "allergy"
})
```

## Configuration

### Settings

The memory system can be configured via `config/settings.py`:

```python
# Memory Configuration
SEMANTIC_MEMORY_ENABLED = True
EPISODIC_MEMORY_ENABLED = True
PROCEDURAL_MEMORY_ENABLED = True
MEMORY_RETRIEVAL_K = 5
MEMORY_SIMILARITY_THRESHOLD = 0.7
```

### Dependencies

Required packages in `requirements.txt`:

```
sentence-transformers==5.0.0
scikit-learn==1.5.2
PyYAML==6.0.1
numpy==1.26.4
```

## Integration with Agents

### Patient Agent
- Uses semantic memory for patient profile management
- Stores episodic memories of successful interactions
- Adapts communication style based on procedural memory

### Text Agent
- Searches semantic memory for relevant context
- Stores text processing episodes
- Optimizes prompts for text analysis tasks

### JSON Agent
- Manages file operations with memory context
- Stores successful file operation episodes
- Adapts file handling based on user preferences

### Web Agent
- Searches semantic memory for relevant web queries
- Stores web search episodes
- Optimizes search strategies based on past success

### Orchestrator Agent
- Routes requests based on memory context
- Stores routing decisions as episodes
- Adapts routing strategies based on outcomes

## Testing

Run the memory system test:

```bash
cd backend_langgraph
python test_memory_system.py
```

This will test all memory types and verify the system is working correctly.

## Migration from LangMem

This system replaces the previous LangMem implementation with:

1. **Simplified architecture** - No complex LangGraph dependencies
2. **Better error handling** - Graceful fallbacks when embeddings unavailable
3. **Improved performance** - Direct file-based storage instead of complex stores
4. **Enhanced flexibility** - Easy to modify and extend memory types
5. **Better integration** - Seamless integration with existing agent tools

## Recommendations

### Memory Strength
- Weigh memory by frequency and recency to prioritize important facts
- Use recent treatment changes as high-priority semantic memories

### Collection vs. Profile Use
- Use profiles for core patient state
- Use collections to track accumulated medical insights or longitudinal trends

### Background Memory Updates
- Run enrichment pass after patient sessions
- Ensure episodic and semantic memory stay fresh without latency impact

### Semantic Relevance Blending
- Combine cosine similarity with metadata filters
- Use `medical_condition: 'diabetes'` for recall precision

## Troubleshooting

### Common Issues

1. **Embedding model not loading**
   - Check internet connection for model download
   - System will fallback to keyword search

2. **Memory files not found**
   - Ensure `data/memory/` directory exists
   - Check file permissions

3. **YAML parsing errors**
   - Verify PyYAML is installed
   - Check YAML syntax in prompt_rules.yaml

### Performance Tips

1. **Limit search results** - Use `limit` parameter to control memory retrieval
2. **Use categories** - Filter semantic searches by category for better precision
3. **Batch operations** - Group related memory updates for better performance
4. **Regular cleanup** - Archive old episodes to maintain performance

## Future Enhancements

- **Memory compression** for long-term storage
- **Cross-patient learning** for population-level insights
- **Real-time memory updates** during conversations
- **Memory visualization** tools for debugging
- **Advanced similarity metrics** beyond cosine similarity 