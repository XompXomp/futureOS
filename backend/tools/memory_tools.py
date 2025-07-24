from langchain.agents import Tool
from modules.memory_operations import MemoryOperations

def create_memory_tools():
    def update_semantic_memory_tool(state: dict) -> dict:
        return MemoryOperations.update_semantic_memory(state)

    def search_semantic_memory_tool(state: dict) -> dict:
        return MemoryOperations.search_semantic_memory(state)

    return [
        Tool(
            name="update_semantic_memory",
            func=update_semantic_memory_tool,
            description="Update semantic memory with new information. Input: state dict."
        ),
        Tool(
            name="search_semantic_memory",
            func=search_semantic_memory_tool,
            description="Search semantic memory. Input: state dict."
        )
    ] 