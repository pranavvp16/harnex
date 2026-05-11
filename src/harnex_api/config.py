from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "dev", "staging", "prod"]


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    env: Environment = Field("local", alias="HARNEX_ENV")
    log_level: str = Field("INFO", alias="HARNEX_LOG_LEVEL")
    api_host: str = Field("0.0.0.0", alias="HARNEX_API_HOST")
    api_port: int = Field(8000, alias="HARNEX_API_PORT")
    # Public-facing hostname (no scheme, no port). Used to allowlist the Host
    # header in the MCP transport-security middleware — without it FastMCP's
    # DNS-rebinding guard rejects requests to non-localhost hosts with
    # "Invalid Host header".
    public_host: str = Field("", alias="HARNEX_PUBLIC_HOST")

    database_url: str = Field(..., alias="DATABASE_URL")

    # Internal URL the API container uses for JWKS fetches and admin REST calls
    # (e.g. http://keycloak:8080 inside docker).
    keycloak_base_url: str = Field("http://localhost:8080", alias="KEYCLOAK_BASE_URL")
    # Public-facing issuer URL — what end users hit and what Keycloak embeds in
    # the `iss` claim. In docker, the SPA reaches Keycloak via the host-published
    # port (http://localhost:8080), so issued tokens carry `iss=http://localhost:8080/...`
    # regardless of the internal docker hostname. Defaults to keycloak_base_url
    # for non-docker setups where both URLs are the same.
    keycloak_issuer_base_url: str = Field("", alias="KEYCLOAK_ISSUER_BASE_URL")
    keycloak_realm: str = Field("harnex", alias="KEYCLOAK_REALM")
    keycloak_audience: str = Field("harnex-api", alias="KEYCLOAK_AUDIENCE")
    keycloak_jwks_cache_seconds: int = Field(300, alias="KEYCLOAK_JWKS_CACHE_SECONDS")
    keycloak_web_client_id: str = Field("harnex-web", alias="KEYCLOAK_WEB_CLIENT_ID")
    keycloak_admin_client_id: str = Field(
        "harnex-admin-cli", alias="KEYCLOAK_ADMIN_CLIENT_ID"
    )
    keycloak_admin_client_secret: SecretStr = Field(
        SecretStr(""), alias="KEYCLOAK_ADMIN_CLIENT_SECRET"
    )

    infisical_base_url: str = Field("http://localhost:8090", alias="INFISICAL_BASE_URL")
    infisical_project_id: str = Field("", alias="INFISICAL_PROJECT_ID")
    infisical_environment: str = Field("dev", alias="INFISICAL_ENVIRONMENT")
    infisical_client_id: SecretStr = Field(SecretStr(""), alias="INFISICAL_CLIENT_ID")
    infisical_client_secret: SecretStr = Field(SecretStr(""), alias="INFISICAL_CLIENT_SECRET")

    # OpenAI embeddings (direct — not Azure). text-embedding-3-large supports MRL
    # truncation via the `dimensions` parameter; 1536d gives best-in-class quality at
    # half the storage of full 3072d and faster pgvector HNSW.
    openai_api_key: SecretStr = Field(SecretStr(""), alias="HARNEX_OPENAI_API_KEY")
    openai_embedding_model: str = Field(
        "text-embedding-3-large", alias="HARNEX_OPENAI_EMBEDDING_MODEL"
    )
    openai_embedding_dim: int = Field(1536, alias="HARNEX_OPENAI_EMBEDDING_DIM")

    blaxel_base_url: str = Field("", alias="BLAXEL_BASE_URL")
    blaxel_api_key: SecretStr = Field(SecretStr(""), alias="BLAXEL_API_KEY")
    blaxel_workspace_url: str = Field("", alias="BLAXEL_WORKSPACE_URL")
    blaxel_workspace: str = Field("", alias="BLAXEL_WORKSPACE")
    blaxel_sandbox_name: str = Field("harnex-execute", alias="BLAXEL_SANDBOX_NAME")
    blaxel_sandbox_image: str = Field("blaxel/node:latest", alias="BLAXEL_SANDBOX_IMAGE")
    blaxel_sandbox_region: str = Field("us-pdx-1", alias="BLAXEL_SANDBOX_REGION")
    blaxel_sandbox_memory_mb: int = Field(2048, alias="BLAXEL_SANDBOX_MEMORY_MB")
    blaxel_default_timeout_seconds: int = Field(30, alias="BLAXEL_DEFAULT_TIMEOUT_SECONDS")

    stripe_api_key: SecretStr = Field(SecretStr(""), alias="STRIPE_API_KEY")
    stripe_webhook_secret: SecretStr = Field(SecretStr(""), alias="STRIPE_WEBHOOK_SECRET")
    razorpay_key_id: SecretStr = Field(SecretStr(""), alias="RAZORPAY_KEY_ID")
    razorpay_key_secret: SecretStr = Field(SecretStr(""), alias="RAZORPAY_KEY_SECRET")
    razorpay_webhook_secret: SecretStr = Field(SecretStr(""), alias="RAZORPAY_WEBHOOK_SECRET")

    use_fake_embeddings: bool = Field(False, alias="HARNEX_USE_FAKE_EMBEDDINGS")
    use_fake_vector_search: bool = Field(False, alias="HARNEX_USE_FAKE_VECTOR_SEARCH")

    # When empty, tenant-create rate limiting falls back to an in-memory deque (dev-only;
    # resets per process and does not coordinate across workers).
    redis_url: str = Field("", alias="HARNEX_REDIS_URL")

    @property
    def is_local(self) -> bool:
        return self.env == "local"


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
