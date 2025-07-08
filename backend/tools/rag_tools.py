# RAG tools 

from langchain.agents import Tool
from modules.rag_operations import RAGOperations
from utils.logging_config import logger

def create_rag_tools():
    """Create RAG operation tools for the agent."""
    
    rag_ops = RAGOperations()
    
    def ask_documents_tool(question: str) -> str:
        """Ask a question based on documents in the knowledge base."""
        try:
            if not question or question.strip() == "":
                return "Error: Please provide a question to ask"
            
            answer = rag_ops.ask_question(question)
            if answer:
                return f"Answer from documents: {answer}"
            else:
                return "Error: Could not get answer from documents"
        except Exception as e:
            return f"Error asking documents: {str(e)}"

    def add_document_tool(content: str) -> str:
        """Add new content to the knowledge base."""
        try:
            if not content or content.strip() == "":
                return "Error: Please provide content to add"
            
            success = rag_ops.add_document_to_vectorstore(content)
            if success:
                return "Successfully added content to knowledge base"
            else:
                return "Error: Could not add content to knowledge base"
        except Exception as e:
            return f"Error adding document: {str(e)}"

    return [
        Tool(
            name="ask_documents",
            func=ask_documents_tool,
            description="Ask a question based on documents in the knowledge base. Input: your question"
        ),
        Tool(
            name="add_document",
            func=add_document_tool,
            description="Add new content to the knowledge base. Input: content to add"
        )
    ]