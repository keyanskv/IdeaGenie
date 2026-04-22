import groq
from typing import List, Dict, Any
from app.models.base import BaseModel
from app.utils.logger import logger

class GroqModel(BaseModel):
    def __init__(self, model_id: str, api_key: str):
        super().__init__(model_id, api_key)
        self.client = groq.Groq(api_key=api_key)

    def generate_response(self, prompt: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            messages = history + [{"role": "user", "content": prompt}]
            
            # Using parameters from user's sample code
            # Note: stream=False for consistent project integration
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=1,
                max_completion_tokens=8192,
                top_p=1,
                reasoning_effort="medium" if "gpt-oss" in self.model_id else None,
                stream=False
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
            logger.error(f"Groq Error: {e}")
            return {"error": str(e)}
