# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Harnex is a multitenant backend that lets agents discover and execute against any HTTP API. First-party connectors (GitHub, Jenkins) and user-supplied OpenAPI / bare-URL connections share a single connector contract.

**The shipped product surface is MCP, not REST.** The MCP server (mounted at `/mcp` in `harnex_api.main`) exposes exactly two tools — `search` and `execute` — defined in `src/harnex_api/mcp/server.py`. Agents authenticate with tenant API keys (`hnx...`) via `Authorization: Bearer`. The `/v1/...` REST routes are **internal/admin only** (used by the console UI); do not treat them as public API. When adding a new capability, ask whether it belongs on the MCP surface or stays REST-only.

## Stack

- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 async, Alembic, Postgres, `uv` for deps
- **Search:** Direct OpenAI embeddings (`text-embedding-3-large`, MRL-truncated to 1536d) + Postgres **pgvector** hybrid search (HNSW cosine + `tsvector`, fused with RRF). Shared `connector_specs` / `operation_chunks` catalog; tenant isolation at query time via JOIN through `connections.spec_id`. Tests use deterministic fakes via `HARNEX_USE_FAKE_EMBEDDINGS` / `HARNEX_USE_FAKE_VECTOR_SEARCH`.
- **Auth:** Keycloak (single `harnex` realm; tenant = organization/group) for console users; tenant-scoped API keys for MCP/REST machine traffic
- **Secrets:** Infisical (third-party platform credentials only — never put Harnex's own secrets here)
- **Sandbox:** Blaxel (workspace runs `blaxel/node:latest`; sandbox name `harnex-execute`) for code-mode execution
- **Console:** `web/` — Vite + React 18 + TanStack Router (file-based routes, generated `routeTree.gen.ts`) + TanStack Query + Tailwind + `oidc-client-ts` for Keycloak PKCE. **Not Next.js.** Deployed via Docker / nginx.

## Commands

### Docker (full stack — recommended for local dev)

```bash
# First-time setup
cp .env.example .env    # fill in POSTGRES_PASSWORD, KEYCLOAK_DB_PASSWORD,
                        # INFISICAL_ENCRYPTION_KEY (exactly 32 chars), INFISICAL_AUTH_SECRET
docker compose build    # build api + web images
docker compose up -d    # start everything

# After Infisical starts, visit http://localhost:8090/admin/signup to create an admin account,
# then create a project + machine identity and fill INFISICAL_CLIENT_ID / INFISICAL_CLIENT_SECRET
# into .env; the api will pick up InfisicalVault automatically on next restart.
```

**Docker gotchas:**
- `DATABASE_URL` in `.env` is for local (non-docker) runs. Docker builds its own URL from `POSTGRES_*` vars — you never need two DATABASE_URL values.
- `INFISICAL_ENCRYPTION_KEY` must be **exactly 32 characters** (raw bytes, not hex). AES-256 needs 32 bytes; a 64-char hex string is 64 bytes and will crash Infisical's KMS init. Generate with `LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 32`.
- If Infisical fails with "Invalid key length" after changing `ENCRYPTION_KEY`, wipe its DB volume (`docker compose stop infisical infisical-db && docker compose rm -f infisical infisical-db && docker volume rm harnex_harnex_infisical_db`) and bring it back up.
- `web/Dockerfile` pins `pnpm@9` to match the lockfile format. Do not bump to `pnpm@latest` — pnpm 10 changed its build-script security model and blocks esbuild, causing the web build to fail.
- When Infisical credentials (`INFISICAL_CLIENT_ID` + `INFISICAL_CLIENT_SECRET` + `INFISICAL_PROJECT_ID`) are not set, the API in `local`/`dev` falls back to `InMemoryVault` and emits a `vault_not_persistent` WARN log — secrets are wiped on restart. In `staging`/`prod` the API refuses to start until those three envs are populated. Fill them and run `uv run python scripts/infisical_smoke.py` to verify wiring.

**Infisical setup (self-host, one-time).**
1. `http://localhost:8090/admin/signup` — create an admin account.
2. Create a project; copy its ID into `INFISICAL_PROJECT_ID`.
3. Project → Access Control → Machine Identities → add a Universal Auth identity. Copy `Client ID` / `Client Secret` into `INFISICAL_CLIENT_ID` / `INFISICAL_CLIENT_SECRET`.
4. `docker compose restart api` → log line should now say `vault backend=infisical`. Run `uv run python scripts/infisical_smoke.py` to round-trip a throwaway secret.

**Moving to Infisical Cloud (dev).** No code changes — same `/api/v3/secrets/raw` API and Universal Auth machine-identity flow.
1. Create the project on `app.infisical.com` (US) or `eu.infisical.com` (EU); the URL determines data residency.
2. Add a Machine Identity (Universal Auth); copy Client ID + Secret.
3. In `.env`: set `INFISICAL_BASE_URL=https://app.infisical.com` (or eu), then `INFISICAL_PROJECT_ID` / `INFISICAL_CLIENT_ID` / `INFISICAL_CLIENT_SECRET` from the Cloud project. Also set `INFISICAL_INTERNAL_BASE_URL` to the same value — docker-compose reads that one for the api service.
4. Restart the API and re-run the smoke script. Connections created against self-host don't migrate automatically — recreate them after the cutover.

**Prod is a separate Infisical Cloud project.** Do not reuse the dev project for prod — a leaked dev token would expose prod creds, since tenant isolation is per-path inside a project, not per-environment. Provision a fresh project + machine identity for prod and wire it via the prod host's environment (NOT this repo's `.env`):
1. New Cloud project `harnex-prod`; capture the project UUID.
2. Machine identity (Universal Auth) with a custom role `harnex-runtime`, scoped to the `prod` environment, `secrets:read/create/update/delete` + `folders:read/create` on `/tenants/**` only. Do **not** grant Admin or workspace-level write.
3. On the prod host: `HARNEX_ENV=prod`, `INFISICAL_BASE_URL=https://app.infisical.com` (+ matching `INFISICAL_INTERNAL_BASE_URL`), `INFISICAL_PROJECT_ID=<prod uuid>`, `INFISICAL_ENVIRONMENT=prod`, `INFISICAL_CLIENT_ID` / `INFISICAL_CLIENT_SECRET` from the prod identity. `INFISICAL_ENCRYPTION_KEY` and `INFISICAL_AUTH_SECRET` are self-host-only — omit on Cloud.
4. With `HARNEX_ENV=prod`, missing Infisical envs RuntimeError on startup (`main.py` lifespan). Verify with `uv run python scripts/infisical_smoke.py` — expect `environment=prod` in the OK line.
5. Verify isolation: the dev machine identity must 401/403 against the prod project UUID. If it doesn't, the role is mis-scoped.

When delegating prod provisioning to another AI agent, hand over a self-contained runbook with the current dev project UUID + client ID listed as "do not touch" — see the prod handoff prompt format used in this repo's history. The agent should never need to edit code; if it does, the ask was misunderstood.

### Backend (run from repo root, non-docker)

```bash
# First-time setup
cp .env.example .env                              # then fill in secrets
docker compose up -d postgres keycloak infisical  # start deps only
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

`tests/conftest.py` forces fake embeddings / fake vector search and sets a dummy `DATABASE_URL`, so `tests/unit` runs without Postgres / live OpenAI / Infisical / Keycloak. Integration tests under `tests/integration` may still hit Postgres — check the file before assuming.

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

## Production deployment (Azure)

Single-VM deployment behind Caddy with auto-TLS, image delivery via Azure Container Registry, GitHub Actions CI/CD with federated OIDC (no static Azure creds in repo secrets).

### Topology

```
Internet  ─→  Caddy (:80/:443, Let's Encrypt)  ─→  api / web / keycloak  (docker network only)
                                                    │
                                                    └─ postgres / keycloak-db / redis  (also internal)
```

Single hostname, path-based routing:

| Path | Service | Notes |
|---|---|---|
| `/` | `web` (nginx serving the Vite SPA bundle) | |
| `/v1/*` | `api` | REST/admin (console UI) |
| `/mcp`, `/mcp/*` | `api` | The shipped product surface |
| `/healthz` | `api` | Used by GH Actions deploy smoke-check |
| `/auth/*` | `keycloak` | `KC_HTTP_RELATIVE_PATH=/auth`; OIDC issuer URL ends in `/auth/realms/harnex` |

`infisical` is **not** part of the prod compose — we use Infisical Cloud. The self-host services from the base compose are parked under the `self-host` profile (only start with `docker compose --profile self-host up`). See the section above for the prod project setup.

### Provisioned resources (current)

Persistent operational handles — not secrets, safe to keep in this file. Capture these from `scripts/azure_provision.sh` output if you ever re-provision:

| Resource | Value |
|---|---|
| Subscription | `Azure subscription 1` (`88134bda-0caf-435b-8108-b5ac3ad89af7`) |
| Tenant | `f5a2aae8-8e2e-4b40-9270-601e8c26f512` |
| Resource group | `harnex-rg` (eastus2) |
| VM | `harnex-vm` — `Standard_D4as_v7` (4 vCPU / 16 GiB), Premium SSD |
| Public IP / FQDN | `harnex-app.eastus2.cloudapp.azure.com` |
| Container registry | `harnexacr.azurecr.io` (Basic SKU) |
| GH Actions identity (OIDC) | `harnex-gh-deploy`, client `89ceef77-5b13-4183-ace4-81ea11a29c99` (AcrPush on `harnexacr`; federated trust on `repo:pranavvp16/harnex:ref:refs/heads/main`) |
| Infisical Cloud project (prod) | `b8d0f796-3e8f-4a32-bc8d-db58c4acb07c` — role `harnex-runtime` (secrets r/w/u/d on `/tenants/**` in `prod` env; folders r/c) |
| Infisical machine identity (prod) | `6adcfc9a-fceb-4fc1-9940-4ad889a55faa` (client ID `a2321c8d-150d-4276-acc3-964d037993d1`) |

The dev Infisical project (`1823b5a4-8477-466a-94a9-c72fce06e21a`) is intentionally separate — see the Infisical section above. **Never** add the dev machine identity to the prod project.

### Files that drive the deployment

- `docker-compose.prod.yml` — override layered on top of `docker-compose.yml`. Pulls api/web images from ACR (no `build:` in prod), removes published ports from everything but Caddy, binds DB volumes to `/data/*`, switches Keycloak to `start --import-realm` with prod hostname/proxy hardening, parks self-host Infisical under the `self-host` profile.
- `infra/caddy/Caddyfile` — single-host routing; Caddy auto-provisions Let's Encrypt for `*.cloudapp.azure.com`.
- `infra/keycloak/post-import.sh` — kcadm patch for the `harnex-web` client (redirectUris, webOrigins, rootUrl/baseUrl) to point at the public host, plus rotates the `harnex-admin-cli` secret away from `change-me-after-import`. **Re-run after any realm re-import.**
- `scripts/azure_provision.sh` — idempotent Azure setup. Re-run is safe — checks before each create.
- `scripts/vm_bootstrap.sh` — runs once on the VM: installs Docker + az CLI, formats and mounts the data disk at `/data`, clones the repo. NVMe-aware data-disk detection.
- `scripts/deploy.sh` — called by `.github/workflows/deploy.yml` over SSH: `az login --identity` → `az acr login` → `docker compose pull api web` → `up -d` → prune.
- `.env.prod.example` — production env template. Real `.env` lives only on the VM at `/opt/harnex/.env` (`chmod 600`).
- `.github/workflows/ci.yml` — backend (ruff + mypy + pytest unit) and frontend (vite build) on PRs. Frontend build uses `pnpm exec vite build` directly because `routeTree.gen.ts` is gitignored and only emitted by the Vite plugin at vite-startup — so `tsc -b` (which `pnpm build` runs first) would fail in a fresh CI checkout.
- `.github/workflows/deploy.yml` — on push to `main`: federated OIDC login → buildx push to ACR (with `${SHA::12}` and `latest` tags) → SSH to VM → run `deploy.sh` → smoke-check `/healthz`.

### GitHub repo secrets (already set on `pranavvp16/harnex`)

| Secret | Purpose |
|---|---|
| `AZURE_CLIENT_ID` | OIDC federated identity (no Azure passwords stored) |
| `AZURE_TENANT_ID` | |
| `AZURE_SUBSCRIPTION_ID` | |
| `ACR_LOGIN_SERVER`, `ACR_NAME` | Registry target |
| `HARNEX_PUBLIC_HOST` | Used in image build args (VITE_*) + healthz smoke check |
| `VM_SSH_HOST`, `VM_SSH_USER`, `VM_SSH_PRIVATE_KEY` | Per-deploy SSH access; user is `azureuser`, key is `~/.ssh/harnex_azure_ed25519` locally |

A read-only **deploy key** (`harnex-vm (read-only)`) is also installed on the repo so the VM can `git pull` over SSH (the repo is private). The VM's `~/.ssh/config` aliases `github.com` to use `~/.ssh/github_deploy`.

### Day-1 (first deploy, one-time)

Already done on this repo; documented for re-creation / disaster recovery.

```bash
# 1. Provision Azure (idempotent — RG, VM, NSG, public IP, ACR, OIDC identity).
GH_REPO=pranavvp16/harnex bash scripts/azure_provision.sh

# 2. Set GitHub repo secrets per the table above using values it prints.

# 3. Bootstrap the VM. The repo is private, so create a read-only deploy key first:
ssh -i ~/.ssh/harnex_azure_ed25519 azureuser@<fqdn> \
    'ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N "" -q && cat ~/.ssh/github_deploy.pub'
# Paste the pubkey into:  gh repo deploy-key add <pubkey-file> --repo pranavvp16/harnex --title "harnex-vm (read-only)"
ssh -i ~/.ssh/harnex_azure_ed25519 azureuser@<fqdn> '
    sudo apt-get install -y git
    sudo git clone git@github.com:pranavvp16/harnex.git /opt/harnex
    sudo chown -R azureuser:azureuser /opt/harnex
    sudo ACR_NAME=harnexacr bash /opt/harnex/scripts/vm_bootstrap.sh
'

# 4. Generate /opt/harnex/.env on the VM from .env.prod.example. Strong randoms for
#    POSTGRES_PASSWORD, KEYCLOAK_DB_PASSWORD, KEYCLOAK_ADMIN_PASSWORD, KEYCLOAK_ADMIN_CLIENT_SECRET.
#    Set HARNEX_PUBLIC_HOST, ACR_LOGIN_SERVER, IMAGE_TAG=latest. Fill OpenAI + Blaxel keys.
#    INFISICAL_BASE_URL=https://app.infisical.com; INFISICAL_PROJECT_ID/CLIENT_ID/CLIENT_SECRET from
#    the harnex-prod Cloud project (above). chmod 600 /opt/harnex/.env.

# 5. First boot, manually (workflow needs ACR to already contain images before its `pull` step works):
#    a) Trigger the deploy workflow once from main — it builds + pushes the images and runs deploy.sh.
#    b) Or, bring up the infrastructure services first and let the deploy workflow seed images:
#         sudo docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps \
#             postgres keycloak-db keycloak redis

# 6. Patch the realm to the public hostname (one-time after first Keycloak boot):
ssh -i ~/.ssh/harnex_azure_ed25519 azureuser@<fqdn> \
    'cd /opt/harnex && sudo -E bash infra/keycloak/post-import.sh'

# 7. Verify:
curl https://<fqdn>/healthz                                       # → {"status":"ok","env":"prod",...}
curl https://<fqdn>/auth/realms/harnex/.well-known/openid-configuration | jq .issuer
# api startup log should contain:  vault backend=infisical base_url=https://app.infisical.com
```

### Day-2 operations

```bash
# SSH (NSG allows :22 from anywhere — strong key auth only)
ssh -i ~/.ssh/harnex_azure_ed25519 azureuser@harnex-app.eastus2.cloudapp.azure.com

# Stack status
sudo docker compose -f /opt/harnex/docker-compose.yml -f /opt/harnex/docker-compose.prod.yml ps

# Tail logs (api / web / caddy / keycloak)
sudo docker compose -f /opt/harnex/docker-compose.yml -f /opt/harnex/docker-compose.prod.yml logs -f api

# Rolling restart (e.g. after editing .env)
sudo docker compose -f /opt/harnex/docker-compose.yml -f /opt/harnex/docker-compose.prod.yml restart api

# Manual redeploy of the latest image already in ACR (without pushing to main)
sudo IMAGE_TAG=latest docker compose -f /opt/harnex/docker-compose.yml -f /opt/harnex/docker-compose.prod.yml pull api web
sudo docker compose -f /opt/harnex/docker-compose.yml -f /opt/harnex/docker-compose.prod.yml up -d

# Roll back to a previous SHA
sudo IMAGE_TAG=<old-sha-12chars> docker compose -f ... pull api web
sudo IMAGE_TAG=<old-sha-12chars> docker compose -f ... up -d

# Persistent data lives at /data (Premium SSD, mounted by vm_bootstrap.sh):
#   /data/postgres, /data/keycloak-db, /data/caddy, /data/caddy-config
# /data/infisical-db is left over from the brief self-host run; safe to ignore.
```

### CI/CD flow

- **Push to any branch / open PR** → `.github/workflows/ci.yml` runs: backend (ruff check + mypy + pytest unit) and frontend (vite build) in parallel.
- **Push to `main`** → `.github/workflows/deploy.yml`:
  1. Federated OIDC login to Azure via `azure/login@v2` (no client secret in GH).
  2. `docker buildx build --push` for `harnex-api` and `harnex-web` to ACR; tagged with `${SHA::12}` and `latest`. The `web` build receives `VITE_*` build args from the `HARNEX_PUBLIC_HOST` secret so the bundle bakes in the right OIDC redirect URL.
  3. SSH to the VM, `git fetch && git checkout <sha>`, then `bash scripts/deploy.sh <tag>`.
  4. `deploy.sh` uses the VM's system-assigned managed identity (AcrPull) — no static ACR creds on the VM.
  5. Smoke check: `curl https://<fqdn>/healthz` retried up to 20× with 5-second backoff.

### Deployment gotchas (real ones we hit)

- **`Standard_D4s_v5` may be capacity-restricted** in eastus2 for some subscriptions (`SkuNotAvailable`). `Standard_D4as_v7` is the AMD-equivalent and was unrestricted; same price tier. Override via `VM_SIZE=...` when running the provision script.
- **NVMe data disks**: D*as_v7 VMs expose attached disks as `/dev/nvme0n2`, not `/dev/sd?`. `vm_bootstrap.sh` scans all whole disks via `lsblk` to handle both.
- **Compose env interpolation runs *before* override merge.** The base `docker-compose.yml` has `KEYCLOAK_BASE_URL: ${KEYCLOAK_INTERNAL_BASE_URL:-http://keycloak:8080}` — setting `KEYCLOAK_INTERNAL_BASE_URL` in the prod override does *not* change the api's `KEYCLOAK_BASE_URL`, because that interpolation has already happened. Override the canonical names (`KEYCLOAK_BASE_URL`, `KEYCLOAK_ISSUER_BASE_URL`) directly in the prod compose.
- **Keycloak 25 deprecated `KC_PROXY`**. Use `KC_PROXY_HEADERS=xforwarded` so X-Forwarded-* from Caddy is honored. With `KC_HOSTNAME_STRICT_HTTPS=true`, Keycloak rejects plain HTTP — that means it won't serve traffic until Caddy is in front of it.
- **`KC_HTTP_RELATIVE_PATH=/auth`** means Keycloak listens on `/auth/...` *inside* the container too. The api needs `KEYCLOAK_BASE_URL=http://keycloak:8080/auth` (note the `/auth` suffix); the Caddyfile uses `handle /auth/*` (NOT `handle_path /auth/*`) so the prefix passes through.
- **Caddyfile `servers { trusted_proxies }`** belongs only in the *global options block* (the unnamed `{ ... }` at the top of the file), never inside a site block — placing it inside causes a parse error and Caddy refuses to start. Caddy is the edge here; we don't need it at all.
- **routeTree.gen.ts is gitignored.** `pnpm build` does `tsc -b && vite build`, but tsc runs first and fails on the missing file. CI calls `pnpm exec vite build` directly so the TanStack Router Vite plugin emits the route tree before bundling. Run the strict `pnpm typecheck` locally.
- **Compose profiles are evaluated *after* env interpolation.** The base compose's self-host `infisical*` services reference `${INFISICAL_ENCRYPTION_KEY:?}` etc. Even though prod puts those services under `profiles: [self-host]` and doesn't start them, compose still parses the interpolations — so the prod `.env` needs placeholder values for `INFISICAL_ENCRYPTION_KEY`, `INFISICAL_AUTH_SECRET`, `INFISICAL_POSTGRES_PASSWORD` (any non-empty string).
- **GH Actions runner IPs are dynamic.** The provision script initially restricts SSH to the operator's `/32`; for the deploy workflow to land, the `allow-ssh` NSG rule is widened to `0.0.0.0/0` (key auth only — Ed25519, no passwords).
- **The repo is private.** The VM clones via SSH using a per-VM **deploy key** (read-only) registered on GitHub, not via the same key used for `ssh azureuser@...`. Don't reuse keys across roles.
- **`docker compose !reset` / `!override` tags require compose v2.24+.** `vm_bootstrap.sh` installs the latest compose-plugin from Docker's apt repo, so this is fine in practice — but Docker Desktop on macOS may ship an older version; validate with `docker compose version`.

### Cost (eastus2, pay-as-you-go)

D4as_v7 ~$140/mo + 2× 64 GiB Premium SSD ~$20/mo + Standard Public IP ~$4/mo + ACR Basic ~$5/mo + low egress ~$5/mo ≈ **$175/mo**. Azure DNS label (`*.cloudapp.azure.com`) is free.

### Out of scope (future hardening)

- **Backups.** Set up Azure Backup on the VM and/or scheduled `pg_dump` → Azure Blob Storage.
- **HA.** Single VM is a SPOF. Migrating to AKS + managed Postgres + Keycloak-on-App-Service is the next step.
- **Monitoring.** Azure Monitor agent + log forwarding not yet wired.
- **Real domain.** When ready, CNAME a real domain at the cloudapp record, update Caddy + Keycloak issuer URL + realm `redirectUris` (5-min change via `post-import.sh`).

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
2. **Index** — `services/ingestion/pipeline.py::index_spec` runs `enrich_spec → operations_to_chunks → embed_batch`, then persists vectors and keyword indexes on shared `ConnectorSpec` / `OperationChunk` rows (pgvector). Status becomes `ready`. Identical specs across tenants reuse the same catalog row (keyed on source identity + `spec_hash` + embedding model/dim).
3. **Search** — MCP `search` tool → `services/search/service.py::SearchService.search` → returns operation candidates with `(operation_id, connection_id, ...)`. If the top hits span multiple connectors it sets `clarification_needed=true` so the agent can disambiguate.
4. **Execute** — MCP `execute` tool → `services/execute/runner.py::execute_structured`:
   - load the `Connection`, build the operation's request from spec + caller params (`services/execute/operation.py`)
   - resolve auth via the connector's `build_auth_context` (secrets pulled from Infisical at request time, not cached)
   - send via `httpx`, write an `Execution` row with status/error/duration
   - return a structured outcome to the caller

Code-mode (LLM-generated JS validators running in the Blaxel sandbox) is the layer **on top of** the structured runner — the structured path is the deterministic fallback. `services/execute/sandbox.py` owns the Blaxel side.

### Data model (Postgres)

Defined in `src/harnex_api/db/models.py`. Key entities:

- `Tenant` (slug, plan, `keycloak_org_id`, `infisical_project_id`, monthly quota)
- `TenantMembership` (links Keycloak users to tenants with a `TenantRole`)
- `Connector` catalog row + `Connection` (one tenant's instance: mode, status, base_url, spec ref, `spec_id` → shared catalog, `auth_flow`, `auth_config`)
- `ConnectorSpec` + `OperationChunk` (cross-tenant OpenAPI catalog + per-operation embeddings / tsvector; tenant scoping only at search/execute via `Connection`)
- `Execution` (one MCP/REST execute call; `mode` ∈ {`code`, `structured`})
- `UsageMonthly` (per tenant per `YYYY-MM` counters; quota enforcement reads this)
- `ApiKey` (tenant-scoped M2M keys; `key_prefix` + `key_hash` — the raw `hnx...` is shown once at creation)
- `OAuthState` (short-lived, deleted after callback)

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

## Health Stack

- typecheck: uv run mypy src && cd web && npx tsc --noEmit
- lint: uv run ruff check . && cd web && npx eslint src
- test: uv run pytest
- deadcode: cd web && npx knip
- shell: (shellcheck not installed — skip)
- gbrain: (not installed — skip)
