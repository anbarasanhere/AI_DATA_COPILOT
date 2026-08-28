from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mysql_host: str = "127.0.0.1"
    mysql_port: int = Field(default=3306, ge=1, le=65535)
    mysql_database: str
    mysql_user: str
    mysql_password: str
    mysql_pool_size: int = Field(default=2, ge=1, le=20)
    mysql_pool_timeout_seconds: int = Field(default=10, ge=1, le=120)
    mysql_connect_timeout_seconds: int = Field(default=5, ge=1, le=120)
    mysql_sample_rows: int = Field(default=5, ge=0, le=100)
    mysql_max_tables: int = Field(default=200, ge=1, le=1000)
    mysql_query_timeout_seconds: int = Field(default=30, ge=1, le=300)
    mysql_max_result_rows: int = Field(default=1000, ge=1, le=10000)
    mysql_output_dir: str = "artifacts"
    llm_provider: str = "none"
    llm_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str | None = None

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
