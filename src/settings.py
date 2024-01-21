import uuid
from functools import cache, cached_property
from typing import Optional, Union

from langchain_core.tracers import LangChainTracer
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = True
        extra = "ignore"
        # allow_mutation = False

    AZURE_OPENAI_API_KEY: str = Field(env="AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_API_BASE: str = Field(env="AZURE_OPENAI_API_BASE")
    AZURE_OPENAI_API_VERSION: str = Field(default="2023-12-01-preview", env="AZURE_OPENAI_API_VERSION")
    AZURE_OPENAI_DEPLOYMENT_VISION: str = Field(default="vision", env="AZURE_OPENAI_DEPLOYMENT_VISION")
    AZURE_OPENAI_DEPLOYMENT_AGENT: str = Field(default="instruct", env="AZURE_OPENAI_DEPLOYMENT_AGENT")

    SERPAPI_API_KEY: Optional[str] = Field(default=None, env="SERPAPI_API_KEY")
    GEOAPIFY_API_KEY: Optional[str] = Field(default=None, env="GEOAPIFY_API_KEY")

    LANGSMITH_ENDPOINT: str = Field(default="https://api.smith.langchain.com", env="LANGSMITH_ENDPOINT")
    LANGSMITH_API_KEY: Optional[str] = Field(default=None, env="LANGSMITH_API_KEY")
    LANGSMITH_PROJECT: str = Field(default="img2card", env="LANGSMITH_PROJECT")

    TELEGRAM_TOKEN: str = Field(env="TELEGRAM_TOKEN")
    TELEGRAM_SECRET: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()).replace("-", ""), env="TELEGRAM_SECRET"
    )
    TELEGRAM_WEBHOOK_URL: Optional[str] = Field(default=None, env="TELEGRAM_WEBHOOK_URL")
    TELEGRAM_DEV_CHAT_ID: Optional[Union[int, str]] = Field(default=None, env="TELEGRAM_DEV_CHAT_ID")

    CONTAINER_APP_NAME: str = Field(default="debug", env="CONTAINER_APP_NAME")

    @computed_field
    @cached_property
    def LANGSMITH_TRACER(self) -> Optional[LangChainTracer]:
        return get_langsmith_tracer(self)


@cache
def get_settings() -> Settings:
    return Settings()


def get_langsmith_tracer(settings) -> Optional[LangChainTracer]:
    if settings.LANGSMITH_API_KEY:
        from langsmith import Client
        return LangChainTracer(
            project_name=settings.LANGSMITH_PROJECT,
            client=Client(api_url=settings.LANGSMITH_ENDPOINT, api_key=settings.LANGSMITH_API_KEY),
        )
    return None
