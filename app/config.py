import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Dict

load_dotenv()

class ModelConfig(BaseModel):
    name: str
    provider: str
    cost_per_1k_tokens_input: float
    cost_per_1k_tokens_output: float

# Estimated costs (subject to change)
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
    "deepseek-coder": ModelConfig(
        name="deepseek-coder",
        provider="deepseek",
        cost_per_1k_tokens_input=0.0001,
        cost_per_1k_tokens_output=0.0002
    ),
    "llama3-70b": ModelConfig(
        name="llama3-70b-8192",
        provider="groq",
        cost_per_1k_tokens_input=0.00059,
        cost_per_1k_tokens_output=0.00079
    ),
    "mixtral-8x7b": ModelConfig(
        name="mixtral-8x7b-32768",
        provider="groq",
        cost_per_1k_tokens_input=0.00027,
        cost_per_1k_tokens_output=0.00027
    ),
    "gpt-oss-120b": ModelConfig(
        name="openai/gpt-oss-120b",
        provider="groq",
        cost_per_1k_tokens_input=0.001, # Estimated
        cost_per_1k_tokens_output=0.002
    )
}

DEFAULT_MODEL = "gpt-4o"

API_KEYS = {
    "openai": os.getenv("OPENAI_API_KEY"),
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "google": os.getenv("GOOGLE_API_KEY"),
    "deepseek": os.getenv("DEEPSEEK_API_KEY"),
    "groq": os.getenv("GROQ_API_KEY"),
}

DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
