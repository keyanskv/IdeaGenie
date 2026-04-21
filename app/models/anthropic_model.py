import anthropic
from typing import List, Dict, Any
from app.models.base import BaseModel
from app.utils.logger import logger

class ClaudeModel(BaseModel):
    def __init__(self, model_id: str, api_key: str):
        super().__init__(model_id, api_key)
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate_response(self, prompt: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            # Anthropic history format is slightly different (doesn't support 'system' in messages list easily without specialized handling)
            # For simplicity, we'll convert 'system' to 'user' or use the 'system' parameter
            system_msg = next((m["content"] for m in history if m["role"] == "system"), "")
            messages = [m for m in history if m["role"] != "system"] + [{"role": "user", "content": prompt}]
            
            response = self.client.messages.create(
                model=self.model_id,
                system=system_msg,
                max_tokens=4096,
                messages=messages
            )
            
            return {
                "content": response.content[0].text,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "model": self.model_id
            }
        except Exception as e:
            logger.error(f"Claude Error: {e}")
            return {"error": str(e)}
