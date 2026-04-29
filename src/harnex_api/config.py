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

    database_url: str = Field(..., alias="DATABASE_URL")

    keycloak_base_url: str = Field("http://localhost:8080", alias="KEYCLOAK_BASE_URL")
    keycloak_realm: str = Field("harnex", alias="KEYCLOAK_REALM")
    keycloak_audience: str = Field("harnex-api", alias="KEYCLOAK_AUDIENCE")
    keycloak_jwks_cache_seconds: int = Field(300, alias="KEYCLOAK_JWKS_CACHE_SECONDS")

    infisical_base_url: str = Field("http://localhost:8090", alias="INFISICAL_BASE_URL")
    infisical_project_id: str = Field("", alias="INFISICAL_PROJECT_ID")
    infisical_environment: str = Field("dev", alias="INFISICAL_ENVIRONMENT")
    infisical_client_id: SecretStr = Field(SecretStr(""), alias="INFISICAL_CLIENT_ID")
    infisical_client_secret: SecretStr = Field(SecretStr(""), alias="INFISICAL_CLIENT_SECRET")

    azure_openai_endpoint: str = Field("", alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: SecretStr = Field(SecretStr(""), alias="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = Field("2024-10-21", alias="AZURE_OPENAI_API_VERSION")
    azure_openai_embedding_deployment: str = Field(
        "text-embedding-3-small", alias="AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
    )
    azure_openai_embedding_dim: int = Field(1536, alias="AZURE_OPENAI_EMBEDDING_DIM")

    azure_search_endpoint: str = Field("", alias="AZURE_SEARCH_ENDPOINT")
    azure_search_api_key: SecretStr = Field(SecretStr(""), alias="AZURE_SEARCH_API_KEY")
    azure_search_index_prefix: str = Field("harnex", alias="AZURE_SEARCH_INDEX_PREFIX")

    azure_storage_connection_string: SecretStr = Field(
        SecretStr(""), alias="AZURE_STORAGE_CONNECTION_STRING"
    )

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

    @property
    def is_local(self) -> bool:
        return self.env == "local"

    def tenant_search_index(self, tenant_id: str) -> str:
        return f"{self.azure_search_index_prefix}-{tenant_id}"


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()  # type: ignore[call-arg]
