# Text processing tools 

from langchain.agents import Tool
from modules.text_operations import TextOperations
from utils.logging_config import logger

def create_text_tools():
    """Create text processing tools for the agent."""
    
    text_ops = TextOperations()
    
    def summarize_text_tool(text: str) -> str:
        """Summarize the provided text."""
        try:
            if not text or text.strip() == "":
                return "Error: Please provide text to summarize"
            
            summary = text_ops.summarize_text(text)
            if summary:
                return f"Summary: {summary}"
            else:
                return "Error: Could not summarize the text"
        except Exception as e:
            return f"Error summarizing text: {str(e)}"

    def answer_question_from_text_tool(input_str: str) -> str:
        """Answer a question based on provided text. Format: 'text|question'"""
        try:
            parts = input_str.split('|', 1)
            if len(parts) != 2:
                return "Error: Please provide input in format 'text|question'"
            
            text, question = parts
            answer = text_ops.answer_question_from_text(text.strip(), question.strip())
            if answer:
                return f"Answer: {answer}"
            else:
                return "Error: Could not answer the question"
        except Exception as e:
            return f"Error answering question: {str(e)}"

    return [
        Tool(
            name="summarize_text",
            func=summarize_text_tool,
            description="Summarize provided text into key points. Input: text to summarize"
        ),
        Tool(
            name="answer_question_from_text",
            func=answer_question_from_text_tool,
            description="Answer a question based on provided text. Input: 'text|question'"
        )
    ]