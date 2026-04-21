import google.generativeai as genai
from typing import List, Dict, Any
from app.models.base import BaseModel
from app.utils.logger import logger

class GeminiModel(BaseModel):
    def __init__(self, model_id: str, api_key: str):
        super().__init__(model_id, api_key)
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_id)

    def generate_response(self, prompt: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            # Convert history to Gemini format
            chat = self.model.start_chat(history=[]) # Simplifying for now
            # Note: Gemini has a specific chat session format. 
            # For a quick implementation, we'll join the context into the prompt or map correctly.
            
            # Mapping:
            gemini_history = []
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                if msg["role"] == "system": continue # Gemini handles system separately
                gemini_history.append({"role": role, "parts": [msg["content"]]})
            
            chat = self.model.start_chat(history=gemini_history)
            response = chat.send_message(prompt)
            
            # Gemini token count is async/separate usually, but we can estimate or use metadata if available
            # For 1.5, usage metadata is often in response
            usage = response.usage_metadata
            
            return {
                "content": response.text,
                "input_tokens": usage.prompt_token_count if usage else 0,
                "output_tokens": usage.candidates_token_count if usage else 0,
                "model": self.model_id
            }
        except Exception as e:
            logger.error(f"Gemini Error: {e}")
            return {"error": str(e)}
