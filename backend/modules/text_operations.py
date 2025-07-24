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
            ("system", (
                "You are a summarization assistant. Summarize the following text in exactly 3 sentences or less.\n"
                "Be concise and capture only the key points.\n"
                "Do NOT add extra information or hallucinate.\n"
                "EXAMPLES:\n"
                "Text: The patient is a 35-year-old male with a history of hypertension. He is currently taking medication and has no known allergies.\n"
                "Output: The patient is a 35-year-old male with hypertension, currently on medication, and has no known allergies.\n"
                "Text: This article discusses the benefits of regular exercise for cardiovascular health.\n"
                "Output: Regular exercise benefits cardiovascular health.\n"
            )),
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
            ("system", (
                "You are a keyword extraction assistant. Extract only the most important keywords from the following text.\n"
                "Return a comma-separated list of keywords.\n"
                "Do NOT add extra information or hallucinate.\n"
                "EXAMPLES:\n"
                "Text: The patient is a 35-year-old male with hypertension and no known allergies.\n"
                "Output: patient, 35-year-old, male, hypertension, no known allergies\n"
                "Text: This article discusses the benefits of regular exercise for cardiovascular health.\n"
                "Output: exercise, cardiovascular health, benefits\n"
            )),
            ("user", "{text}")
        ])
        chain = prompt | llm
        response = chain.invoke({"text": text})
        keywords = str(getattr(response, 'content', response)).strip()
        state['keywords'] = keywords if keywords else 'Keyword extraction failed.'
        return state

    @staticmethod
    def respond_conversationally(state: dict) -> dict:
        text = state.get('text', '')
        from config.settings import settings
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
                temperature=0.3
            )
        from langchain_core.prompts import ChatPromptTemplate
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Respond conversationally to the following user message."),
            ("user", "{text}")
        ])
        chain = prompt | llm
        response = chain.invoke({"text": text})
        reply = str(getattr(response, 'content', response)).strip()
        if reply:
            state['final_answer'] = reply
        else:
            state['final_answer'] = ""
        return state