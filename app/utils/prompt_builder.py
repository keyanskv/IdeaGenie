from typing import List, Dict

class PromptBuilder:
    @staticmethod
    def build_system_prompt(base_prompt: str, context: str = "") -> str:
        if not context:
            return base_prompt
        return f"{base_prompt}\n\nAdditional Context:\n{context}"

    @staticmethod
    def adapt_for_model(prompt: str, model_provider: str) -> str:
        """
        Adjusts prompt style based on model characteristics.
        """
        if model_provider == "anthropic":
            return f"Please respond carefully and concisely. {prompt}"
        if model_provider == "google":
            return f"{prompt}\n\nPlease be helpful and accurate."
        return prompt

    @staticmethod
    def inject_memory(prompt: str, history_summary: str) -> str:
        if not history_summary:
            return prompt
        return f"Past conversation summary: {history_summary}\n\nCurrent query: {prompt}"
