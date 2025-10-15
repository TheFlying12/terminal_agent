"""Configuration management for AI Shell."""

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field


class Config(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""
    
    # Provider settings
    ai_provider: Literal["openai", "ollama"] = Field(default="openai", alias="AI_PROVIDER")
    
    # OpenAI settings
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    
    # Ollama settings
    ollama_host: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_HOST")
    ollama_model: str = Field(default="llama3.1:8b", alias="OLLAMA_MODEL")
    
    # Server settings
    ai_host: str = Field(default="127.0.0.1", alias="AI_HOST")
    ai_port: int = Field(default=8765, alias="AI_PORT")
    
    # Logging settings
    log_path: str = Field(default="~/.ai-shell/audit.jsonl", alias="LOG_PATH")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }
    
    @property
    def expanded_log_path(self) -> Path:
        """Get log path with ~ expanded."""
        return Path(self.log_path).expanduser()
    
    @property
    def server_url(self) -> str:
        """Get full server URL."""
        return f"http://{self.ai_host}:{self.ai_port}"


def load_config() -> Config:
    """Load configuration from .env file and environment variables."""
    # Try to load .env from current directory or parent directories
    env_path = Path(".env")
    if not env_path.exists():
        # Look for .env in parent directories
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            env_candidate = parent / ".env"
            if env_candidate.exists():
                env_path = env_candidate
                break
    
    if env_path.exists():
        load_dotenv(env_path)
    
    return Config()


# Global config instance
config = load_config()
