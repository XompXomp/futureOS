#!/usr/bin/env python3
"""
Test script for the Curor Memory System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.memory_system import CurorMemorySystem
from tools.memory_tools import create_memory_tools
import json

def test_memory_system():
    """Test the Curor Memory System functionality."""
    print("🧠 Testing Curor Memory System...")
    
    # Initialize memory system
    patient_id = "test_patient_001"
    memory_system = CurorMemorySystem(patient_id)
    
    print(f"✅ Memory system initialized for patient: {patient_id}")
    
    # Test semantic memory
    print("\n📝 Testing Semantic Memory...")
    
    # Add some semantic memories
    memory_id1 = memory_system.update_semantic_memory(
        "Patient has Type 2 Diabetes and prefers morning appointments",
        category="medical_condition"
    )
    print(f"✅ Added semantic memory: {memory_id1}")
    
    memory_id2 = memory_system.update_semantic_memory(
        "Patient is allergic to penicillin",
        category="allergy"
    )
    print(f"✅ Added semantic memory: {memory_id2}")
    
    memory_id3 = memory_system.update_semantic_memory(
        "Patient prefers Dr. Smith as their primary care physician",
        category="preference"
    )
    print(f"✅ Added semantic memory: {memory_id3}")
    
    # Test semantic memory search
    print("\n🔍 Testing Semantic Memory Search...")
    results = memory_system.search_semantic_memory("diabetes", limit=3)
    print(f"✅ Found {len(results)} results for 'diabetes'")
    for result in results:
        print(f"   - {result['content']}")
    
    # Test episodic memory
    print("\n📚 Testing Episodic Memory...")
    
    episode_id1 = memory_system.store_episodic_memory(
        interaction_type="symptom_assessment",
        content="Patient reported chest pain and shortness of breath",
        reasoning_context="Used standard cardiac assessment protocol",
        outcome="Referred to cardiologist for further evaluation",
        metadata={"severity": "moderate", "urgency": "high"}
    )
    print(f"✅ Stored episodic memory: {episode_id1}")
    
    episode_id2 = memory_system.store_episodic_memory(
        interaction_type="medication_review",
        content="Reviewed current medications and identified potential interactions",
        reasoning_context="Cross-referenced with drug interaction database",
        outcome="Adjusted metformin dosage and added monitoring schedule",
        metadata={"medications_reviewed": ["metformin", "lisinopril"]}
    )
    print(f"✅ Stored episodic memory: {episode_id2}")
    
    # Test episodic memory search
    print("\n🔍 Testing Episodic Memory Search...")
    episodes = memory_system.search_episodic_memory(limit=5)
    print(f"✅ Found {len(episodes)} episodes")
    for episode in episodes:
        print(f"   - {episode['interaction_type']}: {episode['content'][:50]}...")
    
    # Test procedural memory
    print("\n⚙️ Testing Procedural Memory...")
    
    # Update procedural memory
    memory_system.update_procedural_memory("communication_style", {
        "tone": "professional_empathetic",
        "preferred_analogies": True,
        "technical_level": "moderate"
    })
    print("✅ Updated communication style rules")
    
    memory_system.update_procedural_memory("interaction_patterns", {
        "follow_up_frequency": "weekly",
        "preferred_contact_method": "text",
        "appointment_preferences": "morning"
    })
    print("✅ Updated interaction pattern rules")
    
    # Test procedural memory retrieval
    print("\n🔍 Testing Procedural Memory Retrieval...")
    communication_rules = memory_system.get_procedural_memory("communication_style")
    print(f"✅ Communication rules: {communication_rules}")
    
    # Test prompt optimization
    print("\n🎯 Testing Prompt Optimization...")
    base_prompt = "You are a medical assistant. Help the patient with their health concerns."
    optimized_prompt = memory_system.optimize_prompt(base_prompt, {
        "patient_condition": "diabetes",
        "interaction_type": "medication_review"
    })
    print(f"✅ Optimized prompt: {optimized_prompt[:100]}...")
    
    # Test memory summary
    print("\n📊 Testing Memory Summary...")
    summary = memory_system.get_memory_summary()
    print(f"✅ Memory summary: {summary}")
    
    # Test memory tools
    print("\n🛠️ Testing Memory Tools...")
    memory_tools = create_memory_tools(patient_id)
    print(f"✅ Created {len(memory_tools)} memory tools")
    
    # Test a memory tool
    search_tool = memory_tools[1]  # search_semantic_memory_tool
    result = search_tool({
        "query": "diabetes",
        "category": "medical_condition",
        "limit": 2
    })
    print(f"✅ Tool result: {result}")
    
    print("\n🎉 All tests completed successfully!")
    return True

if __name__ == "__main__":
    try:
        test_memory_system()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 