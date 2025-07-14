# Configuration and environment variables for LangGraph backend

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_PSE_API_KEY = os.getenv("GOOGLE_PSE_API_KEY")
    GOOGLE_PSE_CX = os.getenv("GOOGLE_PSE_CX")  # Custom Search Engine ID
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/database.db")
    
    # RAG Settings
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DOCS_FOLDER = os.path.join(BASE_DIR, "data", "docs")
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    RETRIEVAL_K = 3
    
    # File Paths
    PATIENT_PROFILE_PATH = os.path.join(DOCS_FOLDER, "patient_profile.json")
    
    # Model Settings
    LLM_MODEL = "llama-3.1-8b-instant"  # Much less rate limited
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Ollama Settings (for local models)
    USE_OLLAMA = True #os.getenv("USE_OLLAMA", "true").lower() == "true"
    USE_LOCAL = True
    if (USE_LOCAL):
        OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") # Using model from local machine
        OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    else:  
        OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://mac.futureos.xyz/") # Using model from SLab
        OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.3:70b")
    
    # Retry Settings
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = float(os.getenv("RETRY_DELAY", "2.0"))
    RETRY_BACKOFF = float(os.getenv("RETRY_BACKOFF", "2.0"))
    
    # LangGraph Settings
    MAX_ITERATIONS = 5  # Reduced to prevent loops
    VERBOSE = True
    
    # Memory Configuration (Curor Memory System)
    MEMORY_WINDOW_SIZE = int(os.getenv("MEMORY_WINDOW_SIZE", "10"))
    PERSISTENT_MEMORY = os.getenv("PERSISTENT_MEMORY", "false").lower() == "true"
    MEMORY_FILE_PATH = os.getenv("MEMORY_FILE_PATH", os.path.join(BASE_DIR, "data", "conversation_memory.json"))
    
    # Curor Memory System Configuration
    SEMANTIC_MEMORY_ENABLED = True
    EPISODIC_MEMORY_ENABLED = True
    PROCEDURAL_MEMORY_ENABLED = True
    MEMORY_RETRIEVAL_K = 5
    MEMORY_SIMILARITY_THRESHOLD = 0.7

settings = Settings() 