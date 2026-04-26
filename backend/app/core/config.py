from pydantic_settings import BaseSettings
from typing import Optional, Dict

class Settings(BaseSettings):
    PROJECT_NAME: str = "IdeaGenie AI"
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 1 week
    
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "ideagenie"
    
    # AI Providers
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    SERPER_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()
