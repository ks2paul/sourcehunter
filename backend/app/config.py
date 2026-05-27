from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", validation_alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-4.1-mini", validation_alias="OPENAI_MODEL")
    ai_keyword_expansion_enabled: bool = Field(default=True, validation_alias="AI_KEYWORD_EXPANSION_ENABLED")
    database_path: str = Field(default="data/sourcehunter.sqlite3", validation_alias="SOURCEHUNTER_DB_PATH")
    elimapi_api_key: str | None = Field(default=None, validation_alias="ELIMAPI_API_KEY")
    elimapi_base_url: str = Field(default="https://openapi.elim.asia/v1", validation_alias="ELIMAPI_BASE_URL")
    auth_enabled: bool = Field(default=True, validation_alias="SOURCEHUNTER_AUTH_ENABLED")
    auth_username: str = Field(default="admin", validation_alias="SOURCEHUNTER_AUTH_USERNAME")
    auth_password: str = Field(default="admin123", validation_alias="SOURCEHUNTER_AUTH_PASSWORD")
    auth_session_secret: str = Field(
        default="sourcehunter-local-session-secret",
        validation_alias="SOURCEHUNTER_AUTH_SESSION_SECRET",
    )
    auth_session_ttl_seconds: int = Field(default=60 * 60 * 12, validation_alias="SOURCEHUNTER_AUTH_SESSION_TTL_SECONDS")
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        validation_alias="SOURCEHUNTER_CORS_ORIGINS",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=(".env.local", "../.env.local"),
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
