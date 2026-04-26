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

    def generate_stream(self, prompt: str, history: List[Dict[str, str]]):
        try:
            messages = history + [{"role": "user", "content": prompt}]
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=1,
                max_completion_tokens=8192,
                top_p=1,
                stream=True
            )
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Groq Stream Error: {e}")
            yield f"Error: {str(e)}"
