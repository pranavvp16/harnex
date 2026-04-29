# Harnex API

Multitenant backend that lets agents discover and execute against any HTTP API. First-party connectors (GitHub, Jenkins) and user-supplied OpenAPI/bare-URL connections share one connector contract.

## Stack

- Python 3.12 + FastAPI + Pydantic v2
- Postgres + SQLAlchemy 2.0 async + Alembic
- Keycloak (single `harnex` realm; tenant = organization/group) for console users
- Infisical for third-party platform secrets
- Azure OpenAI embeddings + Azure AI Search for semantic similarity
- Blaxel sandbox for code-mode execution

## Local dev

```bash
cp .env.example .env
docker compose up -d postgres keycloak infisical
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn harnex_api.main:app --reload
```

## Layout

```
src/harnex_api/
  main.py
  config.py
  db/                 # SQLAlchemy models + Alembic
  connectors/         # base, registry, generic, github, jenkins
  auth/               # strategies, keycloak, vault, oauth, injector
  services/
    ingestion/        # fetcher, enricher, chunker, refresher
    search/           # vector_search adapters
    execute/          # codemode, sandbox, error_parser
    tenant/           # provisioner, quota, billing
  api/
    routes/           # search, execute, connections, webhooks
    dependencies/     # auth, tenant, quota
  jobs/
```

## Phase plan

1. Ingestion + search (`/v1/search`)
2. Execute via Blaxel (`/v1/execute`)
3. Auth (Keycloak + Infisical + OAuth)
4. Tenant provisioning + quota + billing
5. Console UI (only after end-to-end demo passes)
