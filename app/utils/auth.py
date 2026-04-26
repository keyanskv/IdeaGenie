def detect_provider(api_key: str) -> str:
    """Detects the AI provider based on the API key prefix."""
    if not api_key:
        return None
        
    if api_key.startswith("gsk_"):
        return "groq"
    elif api_key.startswith("sk-ant-"):
        return "anthropic"
    elif api_key.startswith("sk-"):
        return "openai"
    elif len(api_key) >= 35 and "-" not in api_key: # Rough check for Gemini keys
        return "google"
    elif api_key.startswith("ds-"): # Potential DeepSeek prefix
        return "deepseek"
        
    return None

def is_key_valid_for_provider(api_key: str, provider: str) -> bool:
    """Checks if the API key matches the expected format for a provider."""
    detected = detect_provider(api_key)
    if not detected:
        return True # Can't be sure, so assume valid for now
    return detected == provider
