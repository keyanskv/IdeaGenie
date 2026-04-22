from app.config import MODELS, API_KEYS
from app.models.openai_model import OpenAIModel
from app.models.anthropic_model import ClaudeModel
from app.models.gemini_model import GeminiModel
from app.models.deepseek_model import DeepSeekModel
from app.models.groq_model import GroqModel

def get_model(model_name: str):
    if model_name not in MODELS:
        raise ValueError(f"Model {model_name} not supported.")
    
    config = MODELS[model_name]
    api_key = API_KEYS.get(config.provider)
    
    if config.provider == "openai":
        return OpenAIModel(config.name, api_key)
    elif config.provider == "anthropic":
        return ClaudeModel(config.name, api_key)
    elif config.provider == "google":
        return GeminiModel(config.name, api_key)
    elif config.provider == "deepseek":
        return DeepSeekModel(config.name, api_key)
    elif config.provider == "groq":
        return GroqModel(config.name, api_key)
    else:
        raise ValueError(f"Provider {config.provider} not implemented.")
