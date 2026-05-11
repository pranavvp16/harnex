# Harnex API

Multitenant backend that lets agents discover and execute against any HTTP API. First-party connectors (GitHub, Jenkins) and user-supplied OpenAPI/bare-URL connections share one connector contract.

## Stack

- Python 3.12 + FastAPI + Pydantic v2
- Postgres + SQLAlchemy 2.0 async + Alembic
- Keycloak (single `harnex` realm; tenant = organization/group) for console users
- Infisical for third-party platform secrets
- OpenAI embeddings + Postgres pgvector (hybrid semantic + keyword search)
- Blaxel sandbox for code-mode execution

## Local dev

```bash
cp .env.example .env
docker compose up -d postgres keycloak infisical
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn harnex_api.main:app --reload
```

## Docker stack — full local dev

Runs the API, console, Keycloak, Infisical, and their databases in one command.

```bash
cp .env.example .env          # then fill the *_PASSWORD / *_SECRET fields below
docker compose build          # build api + web images
docker compose up -d          # start everything
```

Required `.env` values (see `.env.example` for the full list):

| Variable | Notes |
|---|---|
| `POSTGRES_PASSWORD` | Any password |
| `KEYCLOAK_DB_PASSWORD` | Any password |
| `KEYCLOAK_ADMIN_PASSWORD` | Login for http://localhost:8080 (user: `admin`) |
| `INFISICAL_POSTGRES_PASSWORD` | Any password |
| `INFISICAL_ENCRYPTION_KEY` | **Exactly 32 chars** (raw ASCII, not hex) — `LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom \| head -c 32` |
| `INFISICAL_AUTH_SECRET` | Any random string |

### Service map

| Service | URL | Notes |
|---|---|---|
| Web console | http://localhost:5173 | Vite/React SPA (nginx) |
| API | http://localhost:8000 | `/healthz` returns ok |
| MCP endpoint | http://localhost:8000/mcp/ | Bearer `hnx...` required |
| Keycloak | http://localhost:8080 | admin / `KEYCLOAK_ADMIN_PASSWORD` |
| Infisical | http://localhost:8090 | first-run signup at `/admin/signup` |
| Postgres | localhost:5432 | `POSTGRES_USER` / `POSTGRES_PASSWORD` |

### Verify the stack

```bash
docker compose ps                                  # all services should be healthy
curl -fsS http://localhost:8000/healthz            # {"status":"ok",...}
docker compose logs api | tail -20                 # look for "Application startup complete"
```

### Verify the MCP endpoint

```bash
# 1. bare /mcp redirects to /mcp/ (307)
curl -si -X POST http://localhost:8000/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' | head -3

# 2. /mcp/ without auth returns JSON-RPC -32001 + 401
curl -si -X POST http://localhost:8000/mcp/ \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":2}' | tail -5

# 3. /mcp/ with a real tenant key (create one via the console or DB) returns the tool list
curl -s -X POST http://localhost:8000/mcp/ \
  -H 'Authorization: Bearer hnx_...' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":3}'
```

### Enable the Infisical-backed vault (optional)

By default the API logs `"backend": "in_memory"` when `INFISICAL_*` credentials are blank — secrets are lost on `api` restart. To persist:

1. Sign up at http://localhost:8090/admin/signup
2. Create a project, then a machine identity (Universal Auth)
3. Set `INFISICAL_PROJECT_ID`, `INFISICAL_CLIENT_ID`, `INFISICAL_CLIENT_SECRET` in `.env`
4. `docker compose restart api`

If Infisical fails with "Invalid key length" after you change `INFISICAL_ENCRYPTION_KEY`, wipe its DB volume:

```bash
docker compose stop infisical infisical-db
docker compose rm -f infisical infisical-db
docker volume rm harnex_harnex_infisical_db
docker compose up -d
```

### Rebuild after backend changes

```bash
docker compose build api && docker compose up -d --force-recreate api
```

The web image only needs rebuilding when frontend code or the `VITE_*` build args change.

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
