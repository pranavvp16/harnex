# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Harnex is a multitenant backend that lets agents discover and execute against any HTTP API. First-party connectors (GitHub, Jenkins) and user-supplied OpenAPI / bare-URL connections share a single connector contract.

**The shipped product surface is MCP, not REST.** The MCP server (mounted at `/mcp` in `harnex_api.main`) exposes exactly two tools — `search` and `execute` — defined in `src/harnex_api/mcp/server.py`. Agents authenticate with tenant API keys (`hnx...`) via `Authorization: Bearer`. The `/v1/...` REST routes are **internal/admin only** (used by the console UI); do not treat them as public API. When adding a new capability, ask whether it belongs on the MCP surface or stays REST-only.

## Stack

- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 async, Alembic, Postgres, `uv` for deps
- **Search:** Azure OpenAI embeddings + Azure AI Search (per-tenant index). Tests use deterministic fakes via `HARNEX_USE_FAKE_EMBEDDINGS` / `HARNEX_USE_FAKE_VECTOR_SEARCH`.
- **Auth:** Keycloak (single `harnex` realm; tenant = organization/group) for console users; tenant-scoped API keys for MCP/REST machine traffic
- **Secrets:** Infisical (third-party platform credentials only — never put Harnex's own secrets here)
- **Sandbox:** Blaxel (workspace runs `blaxel/node:latest`; sandbox name `harnex-execute`) for code-mode execution
- **Console:** `web/` — Vite + React 18 + TanStack Router (file-based routes, generated `routeTree.gen.ts`) + TanStack Query + Tailwind + `oidc-client-ts` for Keycloak PKCE. **Not Next.js.** Deployed via Docker / nginx.

## Commands

### Backend (run from repo root)

```bash
# First-time setup
cp .env.example .env                              # then fill in secrets
docker compose up -d postgres keycloak infisical  # start deps
uv sync --extra dev                               # install deps incl. dev
uv run alembic upgrade head                       # apply migrations

# Run the API
uv run uvicorn harnex_api.main:app --reload

# Tests
uv run pytest                                     # all tests
uv run pytest tests/unit                          # unit only (no infra needed)
uv run pytest tests/integration/test_mcp_smoke.py # one file
uv run pytest -k indexing                         # by keyword
uv run pytest --cov=harnex_api                    # with coverage

# Lint / type-check
uv run ruff check .
uv run ruff format .
uv run mypy src

# Migrations
uv run alembic revision --autogenerate -m "..."
uv run alembic upgrade head
uv run alembic downgrade -1
```

`tests/conftest.py` forces fake embeddings / fake vector search and sets a dummy `DATABASE_URL`, so `tests/unit` runs without Postgres / Azure / Infisical / Keycloak. Integration tests under `tests/integration` may still hit Postgres — check the file before assuming.

### Frontend (run from `web/`)

```bash
pnpm install
pnpm dev          # vite dev server on :5173
pnpm build        # tsc -b && vite build
pnpm typecheck    # tsc -b --noEmit
pnpm lint         # eslint src
```

The TanStack Router plugin regenerates `web/src/routeTree.gen.ts` automatically — do not hand-edit it. Add or remove route files under `web/src/routes/` instead.

### Blaxel sandbox

```bash
uv run python scripts/blaxel_provision.py   # idempotent; reads BLAXEL_* from .env
```

## Architecture

### Connector contract (the spine)

Everything that talks to a remote API goes through `Connector` (`src/harnex_api/connectors/base.py`). Built-ins (`github`, `jenkins`, `generic`) register at import time via `register_builtins()` in `connectors/registry.py`. A `Connector` knows how to:

1. `load_spec` — produce a normalized OpenAPI 3.x doc (or `None` for bare-URL)
2. `infer_base_url` — pick the request base from connection config + spec
3. `build_auth_context` — resolve secrets from the vault and return an `AuthContext` (headers/query/basic) ready for injection
4. `before_execute` — optional last-mile transform of the outbound request

Ingestion, search, and execute all consume this Protocol — adding a new connector means a new subclass, not a new code path. When changing this contract, update **all three** of the built-in connectors (`generic.py`, `github.py`, `jenkins.py`).

### Request lifecycle

1. **Connect** — `POST /v1/connections` (REST/admin) creates a `Connection` row with `mode` ∈ {`builtin`, `openapi_url`, `openapi_upload`, `bare_url`} and an `AuthFlow`. Status starts `pending`.
2. **Index** — `services/ingestion/pipeline.py::index_spec` runs `enrich_spec → operations_to_chunks → embed_batch → vector_search.upsert`. Status becomes `ready`. Each tenant has its own Azure Search index (`Tenant.azure_search_index`).
3. **Search** — MCP `search` tool → `services/search/service.py::SearchService.search` → returns operation candidates with `(operation_id, connection_id, ...)`. If the top hits span multiple connectors it sets `clarification_needed=true` so the agent can disambiguate.
4. **Execute** — MCP `execute` tool → `services/execute/runner.py::execute_structured`:
   - load the `Connection`, build the operation's request from spec + caller params (`services/execute/operation.py`)
   - resolve auth via the connector's `build_auth_context` (secrets pulled from Infisical at request time, not cached)
   - send via `httpx`, write an `Execution` row with status/error/duration
   - return a structured outcome to the caller

Code-mode (LLM-generated JS validators running in the Blaxel sandbox) is the layer **on top of** the structured runner — the structured path is the deterministic fallback. `services/execute/sandbox.py` owns the Blaxel side.

### Data model (Postgres)

Defined in `src/harnex_api/db/models.py`. Key entities:

- `Tenant` (slug, plan, `keycloak_org_id`, `infisical_project_id`, `azure_search_index`, `azure_blob_container`, monthly quota)
- `TenantMembership` (links Keycloak users to tenants with a `TenantRole`)
- `Connector` catalog row + `Connection` (one tenant's instance: mode, status, base_url, spec ref, `auth_flow`, `auth_config`)
- `Execution` (one MCP/REST execute call; `mode` ∈ {`code`, `structured`})
- `UsageMonthly` (per tenant per `YYYY-MM` counters; quota enforcement reads this)
- `ApiKey` (tenant-scoped M2M keys; `key_prefix` + `key_hash` — the raw `hnx...` is shown once at creation)
- `OAuthState` (short-lived, deleted after callback)

`Tenant.azure_search_index` and `Tenant.azure_blob_container` are tenant-scoped resource pointers — never reuse across tenants.

### Auth — three things, kept separate

- **Console users → Keycloak** via OIDC PKCE in the SPA (`web/src/lib/auth.tsx`). Backend verifies JWT, maps user → tenant via `TenantMembership`.
- **MCP / API clients → tenant API keys.** `mcp/server.py` extracts the bearer, looks it up via `services.api_key_auth.authenticate_key`, and sets a `ContextVar` for the tool body. REST uses the same key check via `api/dependencies/auth.py`.
- **Outbound (Harnex → third-party API) → connector auth.** `auth/strategies.py` defines per-flow strategies (`AuthFlow.api_key_header`, `bearer`, `basic`, `oauth_*`); `auth/vault.py` pulls the secret material from Infisical at execute time. Don't bypass strategies — adding a flow means adding a strategy.

### Layout (the parts that aren't obvious)

```
src/harnex_api/
  main.py              # FastAPI app + MCP mount at /mcp
  mcp/server.py        # the shipped surface — exactly two tools
  connectors/          # base contract + builtins + registry
  auth/                # strategies (outbound) + vault loader
  db/                  # SQLAlchemy models + Alembic env (migrations under db/migrations/versions/)
  services/
    ingestion/         # fetcher, enricher, chunker, pipeline (orchestrator)
    search/            # embeddings, vector_search, service (filters, clarification logic)
    execute/           # operation builder, structured runner, sandbox (Blaxel)
  api/
    routes/            # search, execute, connections, connectors, api_keys, executions, usage
    dependencies/      # auth + db session
    schemas/           # request/response Pydantic models
```

## Conventions

- **Async everywhere.** SQLAlchemy is `asyncio`, httpx is `AsyncClient`, FastAPI handlers are `async def`. Don't drop into sync; use `session_scope()` from `db/session.py` outside request scope.
- **Settings.** `harnex_api.config.get_settings()` is `@lru_cache`d — call it; don't read `os.environ` directly. To override in tests, set env *before* import and call `get_settings.cache_clear()` (see `tests/conftest.py`).
- **Ruff config.** Line length 100; selected rules `E F I B UP N SIM RUF`; ignores `E501` (line length already enforced) and `B008` (FastAPI's `Depends(...)` default-arg pattern is intentional). Don't sprinkle `# noqa: B008`.
- **Mypy is strict.** New code must type-check under `mypy src` with `strict = true` + the pydantic plugin.
- **MCP tool docstrings are part of the wire contract.** Agents read them to decide when to call. Edit them with care — concise, behaviorally specific.
- **Tenant scoping is mandatory** on every query that touches tenant data. There is no global admin path; every service takes a `tenant_id` argument.

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Product ideas/brainstorming → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Design system/plan review → invoke /design-consultation or /plan-design-review
- Full review pipeline → invoke /autoplan
- Bugs/errors → invoke /investigate
- QA/testing site behavior → invoke /qa or /qa-only
- Code review/diff check → invoke /review
- Visual polish → invoke /design-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save progress → invoke /context-save
- Resume context → invoke /context-restore
