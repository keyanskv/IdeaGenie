from pydantic import BaseModel
from typing import Optional, List, Any

class AIResponse(BaseModel):
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    error: Optional[str] = None

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    model_id: str = "gpt-4o"
    mode: str = "auto"
    web_search: bool = False
    conversation_id: Optional[str] = None
