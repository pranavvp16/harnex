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
    # A separate sandbox is provisioned for Python-runtime skills (pdf, xlsx,
    # pptx). Splitting by runtime keeps the per-image dep footprint minimal
    # instead of trying to coerce one image to host both stacks.
    blaxel_python_sandbox_name: str = Field(
        "harnex-execute-py", alias="BLAXEL_PYTHON_SANDBOX_NAME"
    )
    blaxel_python_sandbox_image: str = Field(
        "blaxel/py-app:latest", alias="BLAXEL_PYTHON_SANDBOX_IMAGE"
    )

    stripe_api_key: SecretStr = Field(SecretStr(""), alias="STRIPE_API_KEY")
    stripe_webhook_secret: SecretStr = Field(SecretStr(""), alias="STRIPE_WEBHOOK_SECRET")
    razorpay_key_id: SecretStr = Field(SecretStr(""), alias="RAZORPAY_KEY_ID")
    razorpay_key_secret: SecretStr = Field(SecretStr(""), alias="RAZORPAY_KEY_SECRET")
    razorpay_webhook_secret: SecretStr = Field(SecretStr(""), alias="RAZORPAY_WEBHOOK_SECRET")

    use_fake_embeddings: bool = Field(False, alias="HARNEX_USE_FAKE_EMBEDDINGS")
    use_fake_vector_search: bool = Field(False, alias="HARNEX_USE_FAKE_VECTOR_SEARCH")

    # Skill artifact storage. When the Azure account/key are empty we fall back
    # to a filesystem backend that serves bytes via /v1/artifacts/... — only
    # acceptable for local/dev.
    azure_storage_account: str = Field("", alias="HARNEX_AZURE_STORAGE_ACCOUNT")
    azure_storage_key: SecretStr = Field(SecretStr(""), alias="HARNEX_AZURE_STORAGE_KEY")
    azure_storage_container: str = Field(
        "harnex-artifacts", alias="HARNEX_AZURE_STORAGE_CONTAINER"
    )
    local_artifacts_dir: str = Field("artifacts", alias="HARNEX_LOCAL_ARTIFACTS_DIR")
    skill_download_url_ttl_seconds: int = Field(
        900, alias="HARNEX_SKILL_DOWNLOAD_URL_TTL_SECONDS"
    )
    skill_max_artifact_bytes: int = Field(
        25 * 1024 * 1024, alias="HARNEX_SKILL_MAX_ARTIFACT_BYTES"
    )
    skill_execute_timeout_seconds: int = Field(
        120, alias="HARNEX_SKILL_EXECUTE_TIMEOUT_SECONDS"
    )

    # When empty, tenant-create rate limiting falls back to an in-memory deque (dev-only;
    # resets per process and does not coordinate across workers).
    redis_url: str = Field("", alias="HARNEX_REDIS_URL")

    # Confidential-client secret for the BFF (server-side OIDC code exchange + password
    # grant). Required in staging/prod; empty disables cookie auth at /v1/session/*.
    keycloak_web_client_secret: SecretStr = Field(
        SecretStr(""), alias="KEYCLOAK_WEB_CLIENT_SECRET"
    )
    # Public origins. `web_base_url` is where the SPA lives (used to validate / build
    # post-login redirects); `api_base_url` is the externally-reachable API host.
    web_base_url: str = Field("http://localhost:5173", alias="HARNEX_WEB_BASE_URL")
    api_base_url: str = Field("http://localhost:8000", alias="HARNEX_API_BASE_URL")

    session_cookie_name: str = Field("harnex_sid", alias="HARNEX_SESSION_COOKIE_NAME")
    csrf_cookie_name: str = Field("harnex_csrf", alias="HARNEX_CSRF_COOKIE_NAME")
    # Empty = host-only cookie. Set to ".harnex.com" for split-host (app./api.) prod.
    session_cookie_domain: str = Field("", alias="HARNEX_SESSION_COOKIE_DOMAIN")
    session_cookie_secure: bool = Field(True, alias="HARNEX_SESSION_COOKIE_SECURE")
    session_cookie_samesite: Literal["lax", "strict", "none"] = Field(
        "lax", alias="HARNEX_SESSION_COOKIE_SAMESITE"
    )
    # Idle TTL slides forward on each request; absolute TTL is the hard cap.
    session_idle_ttl_seconds: int = Field(
        60 * 60 * 24, alias="HARNEX_SESSION_IDLE_TTL_SECONDS"
    )
    session_absolute_ttl_seconds: int = Field(
        60 * 60 * 24 * 30, alias="HARNEX_SESSION_ABSOLUTE_TTL_SECONDS"
    )
    # CSV of Fernet keys (44-char url-safe base64). First key encrypts new ciphertexts;
    # remaining keys are tried during decrypt for in-flight rotation. Required in
    # staging/prod (lifespan refuses to start without it).
    session_encryption_keys: SecretStr = Field(
        SecretStr(""), alias="HARNEX_SESSION_ENCRYPTION_KEYS"
    )
    # Rollout flag — accept legacy Bearer-JWT auth while the SPA migrates to cookies.
    # Flip to False after the SPA cutover lands.
    allow_bearer_auth: bool = Field(True, alias="HARNEX_ALLOW_BEARER_AUTH")

    @property
    def is_local(self) -> bool:
        return self.env == "local"


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
