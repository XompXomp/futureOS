# RAG functionality 

import os
from typing import Optional
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from config.settings import settings
from utils.logging_config import logger
from dotenv import load_dotenv
load_dotenv()  # This will load .env into os.environ

class RAGOperations:
    def __init__(self):
        self.chain = None
        self.vectorstore = None
        self.setup_rag()

    def setup_rag(self) -> None:
        """Setup RAG system with documents from the docs folder."""
        try:
            if not os.path.exists(settings.DOCS_FOLDER):
                os.makedirs(settings.DOCS_FOLDER)
                logger.warning(f"Created docs folder: {settings.DOCS_FOLDER}")
                return

            # Load documents
            loader = DirectoryLoader(
                settings.DOCS_FOLDER,
                glob="*.json",
                loader_cls=TextLoader,
                show_progress=True
            )
            docs = loader.load()
            
            if not docs:
                logger.warning("No documents found in docs folder")
                return

            logger.info(f"Loaded {len(docs)} documents")

            # Split documents
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            chunks = splitter.split_documents(docs)
            logger.info(f"Created {len(chunks)} chunks")

            # Create embeddings and vector store
            embeddings = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL
            )
            self.vectorstore = FAISS.from_documents(chunks, embeddings)
            logger.info(f"FAISS index created with {self.vectorstore.index.ntotal} vectors")

            # Create retriever
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": settings.RETRIEVAL_K})

            # Create prompt
            system_prompt = """
            You are an assistant that answers questions based on the provided context.
            If the answer is not in the context, say "I don't know based on the provided documents."
            Use at most 3 sentences in your response.
            
            Context: {context}
            """
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", "{input}")
            ])

            # Create LLM and chains
            if settings.USE_OLLAMA:
                llm = ChatOllama(
                    model=settings.OLLAMA_MODEL,
                    base_url=settings.OLLAMA_BASE_URL,
                    temperature=0
                )
            else:
                llm = ChatGroq(
                    model=settings.LLM_MODEL,
                    temperature=0
                )
            
            combine_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
            self.chain = create_retrieval_chain(retriever=retriever, combine_docs_chain=combine_chain)
            
            logger.info("RAG system initialized successfully")
        except Exception as e:
            logger.error(f"Error setting up RAG system: {str(e)}")

    def ask_question(self, question: str) -> Optional[str]:
        """Ask a question using the RAG system."""
        try:
            if self.chain is None:
                logger.warning("RAG system not initialized")
                return "RAG system is not available. Please add documents to the docs folder."

            response = self.chain.invoke({"input": question})
            answer = response.get("answer") or response.get("result")
            
            logger.info(f"RAG question answered: {question}")
            return answer
        except Exception as e:
            logger.error(f"Error asking RAG question: {str(e)}")
            return None

    def add_document_to_vectorstore(self, content: str, metadata: Optional[dict] = None) -> bool:
        """Add a new document to the existing vector store."""
        try:
            if self.vectorstore is None:
                logger.warning("Vector store not initialized")
                return False

            # Create document
            from langchain_core.documents import Document
            doc = Document(page_content=content, metadata=metadata or {})
            
            # Split into chunks
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            chunks = splitter.split_documents([doc])
            
            # Add to vector store
            embeddings = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL
            )
            self.vectorstore.add_documents(chunks)
            
            logger.info(f"Added document to vector store: {len(chunks)} chunks")
            return True
        except Exception as e:
            logger.error(f"Error adding document to vector store: {str(e)}")
            return False