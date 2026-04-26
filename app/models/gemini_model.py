from google import genai
from typing import List, Dict, Any
from app.models.base import BaseModel
from app.utils.logger import logger

class GeminiModel(BaseModel):
    def __init__(self, model_id: str, api_key: str):
        super().__init__(model_id, api_key)
        self.client = genai.Client(api_key=api_key)

    def generate_response(self, prompt: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            # Convert history to google-genai format
            contents = []
            for msg in history:
                if msg["role"] == "system":
                    # Note: System instructions are handled separately in generate_content
                    # but for simplicity we skip or can prepent them. 
                    # Here we follow the previous logic of skipping.
                    continue
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})
            
            # Add current prompt
            contents.append({"role": "user", "parts": [{"text": prompt}]})
            
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=contents
            )
            
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

    def generate_stream(self, prompt: str, history: List[Dict[str, str]]):
        try:
            contents = []
            for msg in history:
                if msg["role"] == "system": continue
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})
            contents.append({"role": "user", "parts": [{"text": prompt}]})
            
            response = self.client.models.generate_content_stream(
                model=self.model_id,
                contents=contents
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Gemini Stream Error: {e}")
            yield f"Error: {str(e)}"
