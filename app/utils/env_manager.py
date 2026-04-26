import os
from pathlib import Path
from dotenv import set_key, load_dotenv

class EnvManager:
    def __init__(self, env_path: str = ".env"):
        self.env_path = Path(env_path)
        if not self.env_path.exists():
            self.env_path.touch()

    def update_key(self, key: str, value: str):
        """Updates or adds a key in the .env file."""
        set_key(str(self.env_path), key, value)
        # Reload environment variables in the current process
        load_dotenv(str(self.env_path), override=True)

    def get_keys(self) -> dict:
        """Returns all relevant AI API keys from the environment."""
        return {
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
            "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY", ""),
            "GROQ_API_KEY": os.getenv("GROQ_API_KEY", ""),
            "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY", ""),
            "SERPER_API_KEY": os.getenv("SERPER_API_KEY", "")
        }

    def is_setup_complete(self) -> bool:
        """Checks if at least one AI API key is configured."""
        keys = self.get_keys()
        return any(v and not v.startswith("your_") for v in keys.values())

env_manager = EnvManager()
