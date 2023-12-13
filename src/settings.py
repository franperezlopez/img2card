from typing import Union
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import cache

class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = True
        # allow_mutation = False
    
    AZURE_OPENAI_API_KEY: str = Field(env="AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_API_BASE: str = Field(env="AZURE_OPENAI_API_BASE")
    AZURE_OPENAI_API_VERSION: str = Field(default="2023-07-01-preview", env="AZURE_OPENAI_API_VERSION")
    AZURE_OPENAI_DEPLOYMENT_VISION: str = Field(default="vision", env="AZURE_OPENAI_DEPLOYMENT_VISION")
    AZURE_OPENAI_DEPLOYMENT_AGENT: str = Field(default="agent", env="AZURE_OPENAI_DEPLOYMENT_AGENT")

    AZURE_COGS_ENDPOINT: str = Field(env="AZURE_COGS_ENDPOINT")
    AZURE_COGS_KEY: str = Field(env="AZURE_COGS_KEY")

    LANGCHAIN_TRACING_V2: str = Field(default="true", env="LANGCHAIN_TRACING_V2")
    LANGCHAIN_ENDPOINT: str = Field(default="https://api.smith.langchain.com", env="LANGCHAIN_ENDPOINT")
    LANGCHAIN_API_KEY: str = Field(env="LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT: str = Field(default="img2card", env="LANGCHAIN_PROJECT")

    TELEGRAM_TOKEN: str = Field(env="TELEGRAM_TOKEN")
    TELEGRAM_DEV_CHAT_ID: Union[int, str] = Field(env="TELEGRAM_DEV_CHAT_ID")


@cache
def get_settings() -> Settings:
    return Settings()
