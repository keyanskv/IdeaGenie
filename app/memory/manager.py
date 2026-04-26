from typing import List, Dict

class ConversationMemory:
    def __init__(self, system_prompt: str = "You are a helpful AI assistant."):
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def get_history(self, max_messages: int = 10) -> List[Dict[str, str]]:
        # Always keep the system prompt
        if len(self.history) <= max_messages + 1:
            return self.history
        
        # Return system prompt + the last max_messages
        return [self.history[0]] + self.history[-(max_messages):]

    def clear(self):
        system_prompt = self.history[0]["content"] if self.history else "You are a helpful AI assistant."
        self.history = [{"role": "system", "content": system_prompt}]

    def summarize(self, summarizer_model):
        """
        Optional: Use an LLM to summarize the history if it gets too long.
        """
        if len(self.history) < 5:
            return
        
        # Placeholder for summarization logic
        pass
