import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings

class WebSearch:
    def __init__(self):
        self.api_key = settings.SERPER_API_KEY
        self.base_url = "https://google.serper.dev/search"

    async def search(self, query: str) -> List[Dict[str, Any]]:
        if not self.api_key:
            return []
        
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {"q": query}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.base_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("organic", [])
            except Exception as e:
                print(f"Search error: {e}")
                return []

    def format_results(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return "No search results found."
        
        formatted = "SEARCH RESULTS:\n"
        for i, res in enumerate(results[:5]):
            formatted += f"[{i+1}] {res.get('title')}\nSource: {res.get('link')}\nSnippet: {res.get('snippet')}\n\n"
        return formatted
