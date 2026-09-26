"""Central application configuration, read once from environment variables."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database. Defaults to a local SQLite file so the hackathon MVP runs with
    # zero setup; point DATABASE_URL at Supabase Postgres for real deployment.
    database_url: str = "sqlite:///./dawa_dost.db"

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # Sarvam
    sarvam_api_key: str = ""
    sarvam_agent_id: str = ""
    sarvam_deployment_id: str = ""
    sarvam_webhook_secret: str = ""

    # App
    next_public_api_url: str = "http://localhost:8000"
    demo_mode: bool = True
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
