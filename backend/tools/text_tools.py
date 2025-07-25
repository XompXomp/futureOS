# Text processing tools 

from langchain.agents import Tool
from modules.text_operations import TextOperations

def create_text_tools():
    def summarize_text_tool(state: dict) -> dict:
        result = TextOperations.summarize_text(state)
        summary = result.get('summary', result.get('error', 'Error'))
        state['summary'] = summary
        state['final_answer'] = summary
        return state

    def extract_keywords_tool(state: dict) -> dict:
        result = TextOperations.extract_keywords(state)
        keywords = result.get('keywords', result.get('error', 'Error'))
        state['keywords'] = keywords
        state['final_answer'] = keywords
        return state

    def respond_conversationally_tool(state: dict) -> dict:
        result = TextOperations.respond_conversationally(state)
        state['final_answer'] = result.get('final_answer', result.get('error', 'Error'))
        return state

    return [
        Tool(
            name="summarize_text",
            func=summarize_text_tool,
            description="Summarize provided text into key points. Input: state dict."
        ),
        Tool(
            name="extract_keywords",
            func=extract_keywords_tool,
            description="Extract key terms from provided text. Input: state dict."
        ),
        Tool(
            name="respond_conversationally",
            func=respond_conversationally_tool,
            description="Respond conversationally to the provided text. Input: state dict."
        )
    ]