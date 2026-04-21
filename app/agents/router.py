from app.config import MODELS
from typing import Optional

class ModelRouter:
    @staticmethod
    def classify_intent(prompt: str) -> str:
        """Classifies the intent of the user prompt."""
        prompt_lower = prompt.lower()
        
        # Coding intent
        coding_keywords = ["python", "javascript", "code", "debug", "function", "class", "implement", "script", "sql", "html"]
        if any(kw in prompt_lower for kw in coding_keywords):
            return "coding"
            
        # Reasoning / Complex intent
        reasoning_keywords = ["analyze", "explain in detail", "reason", "philosophy", "strategy", "complex", "evaluate", "compare"]
        if any(kw in prompt_lower for kw in reasoning_keywords):
            return "reasoning"
            
        # Research / Search intent
        research_keywords = ["research", "find information", "latest news", "search", "who is", "what happened"]
        if any(kw in prompt_lower for kw in research_keywords):
            return "research"
            
        return "casual"

    @staticmethod
    def route_query(prompt: str) -> str:
        intent = ModelRouter.classify_intent(prompt)
        
        if intent == "coding":
            return "deepseek-coder"
        elif intent == "reasoning":
            return "claude-3-5-sonnet"
        elif intent == "research":
            return "gpt-4o" # GPT-4o often better for factual research
        else:
            # Casual or simple
            if len(prompt) < 150:
                return "gemini-1.5-flash"
            return "gpt-4o"
