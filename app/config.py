import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Dict, Optional

load_dotenv(override=True)

class ModelConfig(BaseModel):
    name: str
    provider: str
    cost_per_1k_tokens_input: float
    cost_per_1k_tokens_output: float

class AppConfig:
    # Secret Key for Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-this-in-production")
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_TOKEN")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    SERPER_API_KEY = os.getenv("SERPER_API_KEY")

    # Base URLs
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    # Model Definitions
    MODELS: Dict[str, ModelConfig] = {
        "gpt-4o": ModelConfig(
            name="gpt-4o",
            provider="openai",
            cost_per_1k_tokens_input=0.005,
            cost_per_1k_tokens_output=0.015
        ),
        "claude-3-5-sonnet": ModelConfig(
            name="claude-3-5-sonnet-20240620",
            provider="anthropic",
            cost_per_1k_tokens_input=0.003,
            cost_per_1k_tokens_output=0.015
        ),
        "gemini-1.5-flash": ModelConfig(
            name="gemini-1.5-flash",
            provider="google",
            cost_per_1k_tokens_input=0.000125,
            cost_per_1k_tokens_output=0.000375
        ),
        "deepseek-chat": ModelConfig(
            name="deepseek-chat",
            provider="deepseek",
            cost_per_1k_tokens_input=0.0001,
            cost_per_1k_tokens_output=0.0002
        ),
        "llama3-70b": ModelConfig(
            name="llama-3.3-70b-versatile",
            provider="groq",
            cost_per_1k_tokens_input=0.00059,
            cost_per_1k_tokens_output=0.00079
        ),
    }

    DEFAULT_MODEL = "gpt-4o"

    @classmethod
    def get_api_key(cls, provider: str) -> Optional[str]:
        keys = {
            "openai": cls.OPENAI_API_KEY,
            "anthropic": cls.ANTHROPIC_API_KEY,
            "google": cls.GOOGLE_API_KEY,
            "deepseek": cls.DEEPSEEK_API_KEY,
            "groq": cls.GROQ_API_KEY,
        }
        return keys.get(provider)

# For backward compatibility
MODELS = AppConfig.MODELS
API_KEYS = {
    "openai": AppConfig.OPENAI_API_KEY,
    "anthropic": AppConfig.ANTHROPIC_API_KEY,
    "google": AppConfig.GOOGLE_API_KEY,
    "deepseek": AppConfig.DEEPSEEK_API_KEY,
    "groq": AppConfig.GROQ_API_KEY,
}
DEEPSEEK_BASE_URL = AppConfig.DEEPSEEK_BASE_URL
SERPER_API_KEY = AppConfig.SERPER_API_KEY
