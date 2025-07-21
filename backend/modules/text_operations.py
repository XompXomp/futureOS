# Text processing and summarization 

import json
from config.settings import settings

class TextOperations:
    @staticmethod
    def summarize_text(state: dict) -> dict:
        text = state.get('text', '')
        from langchain_groq import ChatGroq
        from langchain_ollama import ChatOllama
        if settings.USE_OLLAMA:
            llm = ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.3
            )
        else:
            llm = ChatGroq(
                model=settings.LLM_MODEL,
                temperature=0.3,
                max_retries=settings.MAX_RETRIES
            )
        from langchain_core.prompts import ChatPromptTemplate
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Summarize the following text in exactly 3 sentences or less. Make it concise and capture the key points."),
            ("user", "{text}")
        ])
        chain = prompt | llm
        response = chain.invoke({"text": text})
        summary = str(getattr(response, 'content', response)).strip()
        state['summary'] = summary if summary else 'Summarization failed.'
        return state

    @staticmethod
    def extract_keywords(state: dict) -> dict:
        text = state.get('text', '')
        from langchain_groq import ChatGroq
        from langchain_ollama import ChatOllama
        if settings.USE_OLLAMA:
            llm = ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.3
            )
        else:
            llm = ChatGroq(
                model=settings.LLM_MODEL,
                temperature=0.3,
                max_retries=settings.MAX_RETRIES
            )
        from langchain_core.prompts import ChatPromptTemplate
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Extract the most important keywords from the following text."),
            ("user", "{text}")
        ])
        chain = prompt | llm
        response = chain.invoke({"text": text})
        keywords = str(getattr(response, 'content', response)).strip()
        state['keywords'] = keywords if keywords else 'Keyword extraction failed.'
        return state