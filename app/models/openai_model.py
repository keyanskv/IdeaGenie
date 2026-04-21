import openai
from typing import List, Dict, Any
from app.models.base import BaseModel
from app.utils.logger import logger

class OpenAIModel(BaseModel):
    def __init__(self, model_id: str, api_key: str):
        super().__init__(model_id, api_key)
        self.client = openai.OpenAI(api_key=api_key)

    def generate_response(self, prompt: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            messages = history + [{"role": "user", "content": prompt}]
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages
            )
            
            content = response.choices[0].message.content
            usage = response.usage
            
            return {
                "content": content,
                "input_tokens": usage.prompt_tokens,
                "output_tokens": usage.completion_tokens,
                "model": self.model_id
            }
        except Exception as e:
            logger.error(f"OpenAI Error: {e}")
            return {"error": str(e)}
