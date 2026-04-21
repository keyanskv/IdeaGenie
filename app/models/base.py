from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseModel(ABC):
    def __init__(self, model_id: str, api_key: Optional[str] = None):
        self.model_id = model_id
        self.api_key = api_key
        if not self.api_key:
            raise ValueError(f"API key for {model_id} is missing.")

    @abstractmethod
    def generate_response(self, prompt: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Generates a response from the model.
        Returns a dict with 'content', 'input_tokens', and 'output_tokens'.
        """
        pass
