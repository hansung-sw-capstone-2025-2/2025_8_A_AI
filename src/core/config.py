import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    helicone_api_key: str = ""
    upstage_api_key: str = ""
    member_name: str = "default"

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "postgres"
    db_user: str = "postgres"
    db_password: str = ""
    db_pool_min_size: int = 5
    db_pool_max_size: int = 20

    model_haiku: str = "claude-3-5-haiku-20241022"
    model_sonnet: str = "claude-sonnet-4-5-20250929"
    model_opus: str = "claude-sonnet-4-20250514"

    embedding_model: str = "embedding-query"
    embedding_dimension: int = 4096

    ai_module_root: Optional[str] = None

    similarity_min: float = 0.45
    similarity_max: float = 0.80
    concordance_min: float = 0.60
    concordance_max: float = 0.95

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def db_config(self) -> dict:
        return {
            "host": self.db_host,
            "port": self.db_port,
            "database": self.db_name,
            "user": self.db_user,
            "password": self.db_password,
        }

    @property
    def data_dir(self) -> Path:
        if self.ai_module_root:
            return Path(self.ai_module_root) / "data"
        return Path(__file__).parent.parent.parent / "data"

    @property
    def prompts_dir(self) -> Path:
        if self.ai_module_root:
            return Path(self.ai_module_root) / "prompts"
        return Path(__file__).parent.parent.parent / "prompts"

    @property
    def results_dir(self) -> Path:
        if self.ai_module_root:
            return Path(self.ai_module_root) / "results"
        return Path(__file__).parent.parent.parent / "results"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
