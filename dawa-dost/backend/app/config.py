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

    # Sarvam - Document AI / Translate (client.doc_ai / client.text)
    sarvam_api_key: str = ""

    # Sarvam Voice Agents (Samvaad) - https://docs.sarvam.ai/conversations
    # Separate API key from the one above; created at
    # https://indus.sarvam.ai/samvaad/settings/api-key
    sarvam_voice_api_key: str = ""
    sarvam_org_id: str = ""
    sarvam_workspace_id: str = ""
    sarvam_app_id: str = ""  # the deployed voice agent's app id
    sarvam_app_version: int = 1
    sarvam_connection_id: str = ""  # telephony connection (what "deployment id" actually is)
    sarvam_agent_phone_number: str = ""  # the number the agent calls FROM
    # Shared secret we append to our own webhook URL as ?token=... since
    # Sarvam's webhook has no documented signature/verification scheme.
    sarvam_webhook_secret: str = ""
    # Publicly reachable base URL for this backend, used to build the
    # webhook_config.url Sarvam calls back to (must not be localhost).
    public_backend_url: str = ""

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
