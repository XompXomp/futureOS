# Test script for GooglePSESearch web search
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.google_pse_search import GooglePSESearch

if __name__ == "__main__":
    pse = GooglePSESearch()
    query = "current US president"
    #print(f"Testing Google PSE search for query: '{query}'\n")
    results = pse.search(query, num_results=5)
    for i, result in enumerate(results, 1):
        pass
        #print(f"Result {i}:")
        #print(f"  Title: {result['title']}")
        #print(f"  Snippet: {result['snippet']}")
        #print(f"  Link: {result['link']}\n")
    if not results:
        pass
        #print("No results returned.") 