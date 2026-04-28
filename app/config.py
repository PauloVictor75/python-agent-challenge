from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    KB_URL: str = Field(
        default="https://raw.githubusercontent.com/igortce/python-agent-challenge/refs/heads/main/python_agent_knowledge_base.md",
    )
    LLM_PROVIDER: str = Field(default="openai")
    LLM_MODEL: str = Field(default="gpt-4o-mini")
    LLM_BASE_URL: str = Field(default="https://api.openai.com/v1")
    LLM_API_KEY: str = Field(default="")
    MAX_HISTORY_MESSAGES: int = Field(default=5)
    SESSION_TTL_SECONDS: int = Field(default=1800)
    APP_TITLE: str = "LLM Knowledge Base Agent"
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()
