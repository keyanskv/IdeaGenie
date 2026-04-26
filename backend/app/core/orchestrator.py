from typing import List, Dict, Any, AsyncGenerator
from app.models.factory import get_model
from app.utils.search import WebSearch

class AIOrchestrator:
    def __init__(self):
        self.search_tool = WebSearch()

    async def chat_stream(self, user_input: str, model_id: str = "gpt-4o", history: List[Dict[str, str]] = None) -> AsyncGenerator[str, None]:
        """
        An async generator that yields chunks from the specified AI model.
        """
        history = history or []
        
        # 1. Check if model exists and has keys
        model = get_model(model_id)
        if not model:
            yield f"Error: Model {model_id} not supported or API key missing."
            return

        # 2. Generate and yield chunks
        try:
            async for chunk in model.generate_stream(user_input, history):
                yield chunk
        except Exception as e:
            yield f"Error: {str(e)}"
