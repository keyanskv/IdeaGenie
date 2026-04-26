import requests
import json
from typing import List, Dict, Any
from app.config import SERPER_API_KEY
from app.utils.logger import logger

class WebSearch:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or SERPER_API_KEY
        self.base_url = "https://google.serper.dev/search"

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        if not self.api_key:
            logger.warning("Serper API key not found. Web search will be disabled.")
            return []

        payload = json.dumps({
            "q": query,
            "num": num_results
        })
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

        try:
            logger.info(f"Performing web search for: {query}")
            response = requests.post(self.base_url, headers=headers, data=payload)
            response.raise_for_status()
            results = response.json()
            
            formatted_results = []
            if "organic" in results:
                for item in results["organic"][:num_results]:
                    formatted_results.append({
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "snippet": item.get("snippet"),
                        "source": item.get("site")
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []

    def format_results_for_prompt(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return "No relevant web search results found."
            
        formatted_str = "WEB SEARCH RESULTS:\n\n"
        for i, res in enumerate(results):
            formatted_str += f"[{i+1}] {res['title']}\n"
            formatted_str += f"URL: {res['link']}\n"
            formatted_str += f"Snippet: {res['snippet']}\n\n"
        
        return formatted_str
