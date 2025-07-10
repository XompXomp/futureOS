# Google Programmable Search Engine operations

import os
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from config.settings import settings
from utils.logging_config import logger

class GooglePSESearch:
    """Google Programmable Search Engine wrapper for web search functionality."""
    
    def __init__(self):
        self.api_key = settings.GOOGLE_PSE_API_KEY
        self.cx = settings.GOOGLE_PSE_CX
        
        if not self.api_key:
            logger.error("GOOGLE_PSE_API_KEY not found in environment variables")
            raise ValueError("GOOGLE_PSE_API_KEY is required")
        
        if not self.cx:
            logger.error("GOOGLE_PSE_CX not found in environment variables")
            raise ValueError("GOOGLE_PSE_CX is required")
        
        self.service = build("customsearch", "v1", developerKey=self.api_key)
    
    def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Perform a web search using Google PSE."""
        try:
            results = []
            
            # Google PSE allows max 10 results per request, so we need to paginate
            for i in range(0, min(num_results, 100), 10):  # Max 100 results
                start_index = i + 1
                
                search_results = self.service.cse().list(
                    q=query,
                    cx=self.cx,
                    start=start_index,
                    num=min(10, num_results - i)
                ).execute()
                
                if 'items' in search_results:
                    for item in search_results['items']:
                        results.append({
                            'title': item.get('title', ''),
                            'link': item.get('link', ''),
                            'snippet': item.get('snippet', ''),
                            'displayLink': item.get('displayLink', '')
                        })
                
                # If we got fewer results than requested, break
                if len(search_results.get('items', [])) < 10:
                    break
            
            logger.info(f"Google PSE search completed for query: {query[:50]}...")
            return results[:num_results]
            
        except Exception as e:
            logger.error(f"Error performing Google PSE search: {str(e)}")
            return []
    
    def search_documents(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Search and return results in a document-like format."""
        results = self.search(query, num_results)
        
        documents = []
        for result in results:
            documents.append({
                'page_content': f"Title: {result['title']}\n\nSnippet: {result['snippet']}\n\nURL: {result['link']}",
                'metadata': {
                    'title': result['title'],
                    'url': result['link'],
                    'snippet': result['snippet'],
                    'display_link': result['displayLink'],
                    'source': 'google_pse'
                }
            })
        
        return documents 