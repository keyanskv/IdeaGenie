import os
from typing import Dict, Any, Optional
from app.core.config import settings

class BaseAIModel:
    async def generate_stream(self, prompt: str, history: list):
        raise NotImplementedError()

class OpenAIModel(BaseAIModel):
    def __init__(self, api_key: str, model_id: str):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
        self.model_id = model_id

    async def generate_stream(self, prompt: str, history: list):
        messages = history + [{"role": "user", "content": prompt}]
        stream = await self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            stream=True
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

class GroqModel(BaseAIModel):
    def __init__(self, api_key: str, model_id: str):
        from groq import AsyncGroq
        self.client = AsyncGroq(api_key=api_key)
        self.model_id = model_id

    async def generate_stream(self, prompt: str, history: list):
        messages = history + [{"role": "user", "content": prompt}]
        stream = await self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            stream=True
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

def get_model(model_id: str, api_key: Optional[str] = None):
    # Mapping model IDs to providers
    if "gpt" in model_id:
        return OpenAIModel(api_key or settings.OPENAI_API_KEY, model_id)
    if "llama" in model_id or "mixtral" in model_id:
        return GroqModel(api_key or settings.GROQ_API_KEY, model_id)
    # Add more providers here (Gemini, Claude, etc.)
    return None
