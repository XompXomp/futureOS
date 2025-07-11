# Test script to verify LangGraph backend structure

import os
import sys

def test_imports():
    """Test that all modules can be imported."""
    try:
        # Test config
        from config import settings
        print("✓ Config module imported successfully")
        
        # Test utils
        from utils import logging_config
        print("✓ Utils module imported successfully")
        
        # Test state
        from state import schema
        print("✓ State module imported successfully")
        
        # Test nodes
        from nodes import input_processor, memory_retriever, llm_router, response_generator
        print("✓ Nodes modules imported successfully")
        
        # Test tools
        from tools import patient_tools, file_tools, web_search_tools, text_tools
        print("✓ Tools modules imported successfully")
        
        # Test graph
        from graph import patient_graph
        print("✓ Graph module imported successfully")
        
        print("\n🎉 All modules imported successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_structure():
    """Test the file structure."""
    expected_files = [
        "requirements.txt",
        "main.py",
        "README.md",
        "__init__.py",
        "config/__init__.py",
        "config/settings.py",
        "utils/__init__.py",
        "utils/logging_config.py",
        "state/__init__.py",
        "state/schema.py",
        "nodes/__init__.py",
        "nodes/input_processor.py",
        "nodes/memory_retriever.py",
        "nodes/llm_router.py",
        "nodes/response_generator.py",
        "tools/__init__.py",
        "tools/patient_tools.py",
        "tools/file_tools.py",
        "tools/web_search_tools.py",
        "tools/text_tools.py",
        "graph/__init__.py",
        "graph/patient_graph.py"
    ]
    
    missing_files = []
    for file_path in expected_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✓ All expected files present")
        return True

def main():
    """Run all tests."""
    print("Testing LangGraph backend structure...\n")
    
    structure_ok = test_structure()
    imports_ok = test_imports()
    
    if structure_ok and imports_ok:
        print("\n🎉 All tests passed! LangGraph backend is ready.")
    else:
        print("\n❌ Some tests failed. Please check the structure.")

if __name__ == "__main__":
    main() 