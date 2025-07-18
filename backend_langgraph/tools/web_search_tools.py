# Google PSE search tools for LangGraph

from langchain.agents import Tool
from typing import Dict, Any, Optional
from utils.logging_config import logger
from config.settings import settings
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import numpy as np

# Import the Google PSE search module
try:
    from modules.google_pse_search import GooglePSESearch
    google_pse_available = True
except ImportError:
    logger.warning("Google PSE search module not available. Web search tools will be disabled.")
    google_pse_available = False

def get_llm():
    """Get LLM instance based on settings."""
    if settings.USE_OLLAMA:
        return ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.1
        )
    else:
        return ChatGroq(
            model=settings.LLM_MODEL,
            temperature=0.1
        )

def get_embeddings():
    """Get embeddings instance using HuggingFaceEmbeddings like the existing codebase."""
    return HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'}
    )

def extract_search_query_llm(user_input: str) -> str:
    """Extract search query using LLM-based semantic understanding."""
    try:
        # Validate input
        if not user_input or user_input.strip() == "":
            logger.warning("Empty user input provided to extract_search_query_llm")
            return ""
        
        llm = get_llm()
        
        prompt = f"""
        Extract a search query from the following user input. 
        Focus on the main topic or question being asked.
        Return only the search query, nothing else.
        
        User input: {user_input}
        """
        
        response = llm.invoke(prompt)
        
        # Extract content from response - handle different response formats
        query = ""
        if hasattr(response, 'content'):
            query = str(response.content).strip()
        else:
            # Try to extract from string representation
            response_str = str(response)
            if 'content=' in response_str and '"' in response_str:
                # Extract content between quotes after content=
                start = response_str.find('content=') + 8
                if start < len(response_str):
                    # Find the first quote after content=
                    quote_start = response_str.find('"', start)
                    if quote_start != -1:
                        # Find the closing quote
                        quote_end = response_str.find('"', quote_start + 1)
                        if quote_end != -1:
                            query = response_str[quote_start + 1:quote_end]
                        else:
                            query = response_str[quote_start + 1:]
                    else:
                        query = response_str[start:]
                else:
                    query = response_str
            else:
                query = response_str
        
        # Clean up the response
        if query.startswith("Search query:"):
            query = query.replace("Search query:", "").strip()
        
        # Validate extracted query
        if not query or query.strip() == "":
            logger.warning(f"LLM returned empty query for input: '{user_input}'")
            # Fallback to user input
            query = user_input.strip()
        
        logger.info(f"LLM extracted search query: '{query}' from input: '{user_input}'")
        return query
        
    except Exception as e:
        logger.error(f"Error extracting search query with LLM: {str(e)}")
        # Fallback to simple extraction
        fallback_query = user_input.strip()
        if not fallback_query:
            logger.warning("Both LLM extraction and fallback failed - returning empty string")
            return ""
        return fallback_query

def create_semantic_search_index(documents: list) -> Optional[FAISS]:
    """Create a semantic search index from documents."""
    try:
        embeddings = get_embeddings()
        
        # Extract text content from documents
        texts = []
        metadatas = []
        
        for doc in documents:
            if isinstance(doc, dict):
                if 'page_content' in doc:
                    texts.append(doc['page_content'])
                    metadatas.append(doc.get('metadata', {}))
                elif 'snippet' in doc:
                    texts.append(doc['snippet'])
                    metadatas.append({
                        'title': doc.get('title', ''),
                        'url': doc.get('link', ''),
                        'source': 'google_pse'
                    })
        
        if not texts:
            return None
        
        # Create FAISS index
        vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
        return vectorstore
        
    except Exception as e:
        logger.error(f"Error creating semantic search index: {str(e)}")
        return None

def semantic_search_documents(query: str, documents: list, top_k: int = 3) -> list:
    """Perform semantic search on documents using vector similarity."""
    try:
        vectorstore = create_semantic_search_index(documents)
        
        if not vectorstore:
            return documents[:top_k]  # Fallback to first k documents
        
        # Perform semantic search
        results = vectorstore.similarity_search_with_score(query, k=top_k)
        
        # Format results
        semantic_results = []
        for doc, score in results:
            semantic_results.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'similarity_score': float(score)
            })
        
        logger.info(f"Semantic search completed for query: '{query}' with {len(semantic_results)} results")
        return semantic_results
        
    except Exception as e:
        logger.error(f"Error performing semantic search: {str(e)}")
        return documents[:top_k]  # Fallback to first k documents

def create_google_pse_tools():
    """Create Google PSE search tools for the agent."""
    
    if not google_pse_available:
        return []
    
    google_pse = GooglePSESearch()
    
    def web_search_tool(query: str) -> str:
        """Search the web using Google PSE with LLM query extraction."""
        try:
            if not query or query.strip() == "":
                return "Error: Please provide a search query"
            
            #--------------------------CULPRIT----------------------------
            # Use LLM to extract and refine the search query
            #refined_query = extract_search_query_llm(query)
            # Use raw query instead
            refined_query = query
            #--------------------------CULPRIT----------------------------

            # Validate refined query before making API call
            if not refined_query or refined_query.strip() == "":
                return "Error: Could not extract a valid search query. Please provide a more specific search term."
            
            results = google_pse.search(refined_query, num_results=5)
            
            if not results:
                return f"No search results found for query: '{refined_query}'"
            
            # Perform semantic search on results
            semantic_results = semantic_search_documents(refined_query, results, top_k=3)
            
            formatted_results = f"Web Search Results (Semantic Search):\n\n"
            for i, result in enumerate(semantic_results, 1):
                if 'content' in result:
                    # Semantic search result
                    formatted_results += f"{i}. {result['metadata'].get('title', 'No title')}\n"
                    formatted_results += f"   URL: {result['metadata'].get('url', 'No URL')}\n"
                    formatted_results += f"   Content: {result['content'][:200]}...\n"
                    formatted_results += f"   Similarity Score: {result['similarity_score']:.3f}\n\n"
                else:
                    # Regular search result
                    formatted_results += f"{i}. {result['title']}\n"
                    formatted_results += f"   URL: {result['link']}\n"
                    formatted_results += f"   Snippet: {result['snippet']}\n\n"
            
            return formatted_results
        except Exception as e:
            return f"Error performing web search: {str(e)}"
    
    def search_documents_tool(query: str) -> str:
        """Search and return documents using semantic search."""
        try:
            if not query or query.strip() == "":
                return "Error: Please provide a search query"
            
            #--------------------------CULPRIT----------------------------
            # Use LLM to extract and refine the search query
            #refined_query = extract_search_query_llm(query)
            # Use raw query instead
            refined_query = query
            #--------------------------CULPRIT----------------------------
            
            # Validate refined query before making API call
            if not refined_query or refined_query.strip() == "":
                return "Error: Could not extract a valid search query. Please provide a more specific search term."
            
            documents = google_pse.search_documents(refined_query, num_results=5)
            
            if not documents:
                return f"No documents found for query: '{refined_query}'"
            
            # Perform semantic search on documents
            semantic_results = semantic_search_documents(refined_query, documents, top_k=3)
            
            formatted_results = f"Semantic Search Documents:\n\n"
            for i, result in enumerate(semantic_results, 1):
                formatted_results += f"Document {i} (Similarity: {result['similarity_score']:.3f}):\n"
                formatted_results += f"{result['content']}\n\n"
            
            return formatted_results
        except Exception as e:
            return f"Error searching documents: {str(e)}"
    
    return [
        Tool(
            name="web_search",
            func=web_search_tool,
            description="Search the web for current information using semantic search. Input: your search query"
        ),
        Tool(
            name="search_documents",
            func=search_documents_tool,
            description="Search the web and return results using semantic similarity. Input: your search query"
        )
    ]

def search_web(state: Dict[str, Any]) -> Dict[str, Any]:
    """Search the web for information using Google PSE with LLM-driven query extraction."""
    
    #print("[DEBUG] search_web tool called with state:", state)
    logger.info(f"[DEBUG] search_web tool called with state: {state}")
    try:
        # Handle different input formats
        user_input = ""
        if isinstance(state, dict):
            # Try different possible keys for user input
            user_input = (state.get("user_input") or 
                         state.get("question") or 
                         state.get("query") or 
                         state.get("text") or 
                         "")
            
            # If we have a question or query, use it directly
            if not user_input and "question" in state:
                user_input = state["question"]
            elif not user_input and "query" in state:
                user_input = state["query"]
        
        # If still no user input, try to extract from the entire state
        if not user_input:
            # Look for any string value that might be the query
            for key, value in state.items():
                if isinstance(value, str) and value.strip():
                    user_input = value
                    break
        
        if not google_pse_available:
            state["error_message"] = "Google PSE search is not available. Please check your configuration."
            state["has_error"] = True
            return state
        
        #--------------------------CULPRIT----------------------------
        # Use LLM to extract and refine the search query
        #refined_query = extract_search_query_llm(query)
        # Use raw query instead
        search_query = user_input
        #--------------------------CULPRIT----------------------------
        
        # Validate search query before making API call
        if not search_query or search_query.strip() == "":
            # Use the entire user input as search query
            search_query = user_input
        
        # Final validation - if still empty, return error
        if not search_query or search_query.strip() == "":
            state["error_message"] = "Could not extract a valid search query. Please provide a more specific search term."
            state["has_error"] = True
            return state
        
        google_pse = GooglePSESearch()
        results = google_pse.search(search_query, num_results=5)
        
        if not results:
            state["search_results"] = []
            state["search_query"] = search_query
            state["search_message"] = f"No search results found for query: '{search_query}'"
            return state
        
        # Perform semantic search on results
        semantic_results = semantic_search_documents(search_query, results, top_k=5)
        
        # Format results with better structure
        results_text = f"Web search results for '{search_query}':\n\n"
        for i, result in enumerate(semantic_results, 1):
            if 'content' in result:
                # Semantic search result
                title = result['metadata'].get('title', 'No title')
                url = result['metadata'].get('url', 'No URL')
                content = result['content'][:300]  # Increased content length
                score = result['similarity_score']
                
                results_text += f"{i}. {title}\n"
                results_text += f"   Source: {url}\n"
                results_text += f"   Summary: {content}\n"
                results_text += f"   Relevance: {score:.3f}\n\n"
            else:
                # Regular search result
                results_text += f"{i}. {result['title']}\n"
                results_text += f"   Source: {result['link']}\n"
                results_text += f"   Summary: {result['snippet']}\n\n"
        
        # Add tool result to state
        tool_results = state.get("tool_results", [])
        tool_results.append({
            "tool": "search_web",
            "output": f"Web search completed for '{search_query}' using LLM-driven query extraction and semantic search. Found {len(semantic_results)} relevant results."
        })
        state["tool_results"] = tool_results
        state["search_results"] = semantic_results
        state["search_query"] = search_query
        state["search_message"] = results_text
        
        #print("[DEBUG] search_web tool result:", results_text)
        logger.info(f"[DEBUG] search_web tool result: {results_text}")
        logger.info(f"Web search completed with LLM-driven query extraction for query: {search_query}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error performing web search: {str(e)}")
        state["error_message"] = f"Error performing web search: {str(e)}"
        state["has_error"] = True
        return state

def search_documents(state: Dict[str, Any]) -> Dict[str, Any]:
    """Search and return documents using Google PSE with semantic search."""
    
    try:
        # Handle different input formats
        user_input = ""
        if isinstance(state, dict):
            # Try different possible keys for user input
            user_input = (state.get("user_input") or 
                         state.get("question") or 
                         state.get("query") or 
                         state.get("text") or 
                         "")
            
            # If we have a question or query, use it directly
            if not user_input and "question" in state:
                user_input = state["question"]
            elif not user_input and "query" in state:
                user_input = state["query"]
        
        # If still no user input, try to extract from the entire state
        if not user_input:
            # Look for any string value that might be the query
            for key, value in state.items():
                if isinstance(value, str) and value.strip():
                    user_input = value
                    break
        
        if not google_pse_available:
            state["error_message"] = "Google PSE search is not available. Please check your configuration."
            state["has_error"] = True
            return state
        
        #--------------------------CULPRIT----------------------------
        # Use LLM to extract and refine the search query
        #refined_query = extract_search_query_llm(query)
        # Use raw query instead
        search_query = user_input
        #--------------------------CULPRIT----------------------------
        
        # Validate search query before making API call
        if not search_query or search_query.strip() == "":
            # Use the entire user input as search query
            search_query = user_input
        
        # Final validation - if still empty, return error
        if not search_query or search_query.strip() == "":
            state["error_message"] = "Could not extract a valid search query. Please provide a more specific search term."
            state["has_error"] = True
            return state
        
        google_pse = GooglePSESearch()
        documents = google_pse.search_documents(search_query, num_results=5)
        
        if not documents:
            state["documents"] = []
            state["search_query"] = search_query
            state["documents_message"] = f"No documents found for query: '{search_query}'"
            return state
        
        # Perform semantic search on documents
        semantic_results = semantic_search_documents(search_query, documents, top_k=3)
        
        # Format documents with better structure
        documents_text = f"Documents found for '{search_query}':\n\n"
        for i, result in enumerate(semantic_results, 1):
            content = result['content'][:400]  # Increased content length
            score = result['similarity_score']
            
            documents_text += f"Document {i} (Relevance: {score:.3f}):\n"
            documents_text += f"{content}\n\n"
        
        # Add tool result to state
        tool_results = state.get("tool_results", [])
        tool_results.append({
            "tool": "search_documents",
            "output": f"Document search completed for '{search_query}' using LLM-driven query extraction and semantic search. Found {len(semantic_results)} relevant documents."
        })
        state["tool_results"] = tool_results
        state["documents"] = semantic_results
        state["search_query"] = search_query
        state["documents_message"] = documents_text
        
        logger.info(f"Document search completed with LLM-driven query extraction for query: {search_query}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        state["error_message"] = f"Error searching documents: {str(e)}"
        state["has_error"] = True
        return state 