# Text processing and summarization 

import time
from typing import Optional
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from config.settings import settings
from utils.logging_config import logger
from dotenv import load_dotenv
load_dotenv()  # This will load .env into os.environ

class TextOperations:
    def __init__(self):
        if settings.USE_OLLAMA:
            self.llm = ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.3
            )
        else:
            self.llm = ChatGroq(
                model=settings.LLM_MODEL,
                temperature=0.3,
                max_retries=settings.MAX_RETRIES
            )

    def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry function with exponential backoff."""
        for attempt in range(settings.MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if "rate limit" in str(e).lower() or "retry" in str(e).lower():
                    if attempt < settings.MAX_RETRIES - 1:
                        wait_time = settings.RETRY_DELAY * (settings.RETRY_BACKOFF ** attempt)
                        logger.warning(f"Rate limit hit, retrying in {wait_time:.1f} seconds... (attempt {attempt + 1}/{settings.MAX_RETRIES})")
                        time.sleep(wait_time)
                        continue
                raise e
        return func(*args, **kwargs)  # Final attempt

    def summarize_text(self, text: str, max_sentences: int = 3) -> Optional[str]:
        """Summarize text using LLM."""
        try:
            if not isinstance(text, str):
                logger.error("Input text must be a string.")
                return None
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"Summarize the following text in exactly {max_sentences} sentences or less. "
                          "Make it concise and capture the key points."),
                ("user", "{text}")
            ])
            
            chain = prompt | self.llm
            response = self._retry_with_backoff(chain.invoke, {"text": text})
            
            summary = response.content.strip() if isinstance(response.content, str) else str(response.content).strip()
            logger.info("Successfully summarized text")
            return summary
        except Exception as e:
            logger.error(f"Error summarizing text: {str(e)}")
            return None

    def extract_key_information(self, text: str, context: str = "") -> Optional[str]:
        """Extract key information from text based on context."""
        try:
            if not isinstance(text, str):
                logger.error("Input text must be a string.")
                return None
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"Extract the most important information from the following text. "
                          f"Context: {context}. Focus on actionable items, dates, names, and key facts."),
                ("user", "{text}")
            ])
            
            chain = prompt | self.llm
            response = self._retry_with_backoff(chain.invoke, {"text": text})
            
            extracted_info = response.content.strip() if isinstance(response.content, str) else str(response.content).strip()
            logger.info("Successfully extracted key information")
            return extracted_info
        except Exception as e:
            logger.error(f"Error extracting key information: {str(e)}")
            return None

    def answer_question_from_text(self, text: str, question: str) -> Optional[str]:
        """Answer a specific question based on provided text."""
        try:
            if not isinstance(text, str) or not isinstance(question, str):
                logger.error("Text and question must be strings.")
                return None
            prompt = ChatPromptTemplate.from_messages([
                ("system", "Answer the following question based only on the provided text. "
                          "If the answer is not in the text, say 'I cannot find that information in the provided text.'"),
                ("user", "Text: {text}\n\nQuestion: {question}")
            ])
            
            chain = prompt | self.llm
            response = self._retry_with_backoff(chain.invoke, {"text": text, "question": question})
            
            answer = response.content.strip() if isinstance(response.content, str) else str(response.content).strip()
            logger.info("Successfully answered question from text")
            return answer
        except Exception as e:
            logger.error(f"Error answering question from text: {str(e)}")
            return None