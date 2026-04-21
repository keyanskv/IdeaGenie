from app.config import MODELS

class ModelRouter:
    @staticmethod
    def route_query(prompt: str) -> str:
        prompt_lower = prompt.lower()
        
        # Coding detection
        coding_keywords = ["python", "javascript", "code", "debug", "function", "class", "implement", "script"]
        if any(kw in prompt_lower for kw in coding_keywords):
            return "deepseek-coder"
        
        # Complex reasoning / Long form
        reasoning_keywords = ["analyze", "explain in detail", "reason", "philosophy", "strategy", "complex"]
        if any(kw in prompt_lower for kw in reasoning_keywords):
            return "claude-3-5-sonnet"
        
        # Simple/Fast
        simple_keywords = ["hello", "hi", "what is", "tell me a joke", "summarize"]
        if any(kw in prompt_lower for kw in simple_keywords) or len(prompt) < 100:
            return "gemini-1.5-flash"
            
        return "gpt-4o"
