# TODOS

Work items from `/devex-review` (2026-05-07).

---

## TODO 1: Seed dev tenant on first startup

**What:** Add a startup hook (Alembic migration data seed, `docker-compose` post-start command, or FastAPI startup event) that ensures the dev tenant `11111111-1111-1111-1111-111111111111` exists in the `tenants` table when `HARNEX_ENV=local`.

**Why:** The console auto-authenticates with a hardcoded dev tenant UUID. When the tenant row is missing, every POST/PUT/DELETE fails with a SQLAlchemy `IntegrityError` (foreign key violation) that bubbles up as an uncaught 500. The console is completely read-only — no API key creation, no connection creation, no execution.

**Pros:** Console becomes fully functional out of the box. Eliminates the #1 blocker in the developer getting-started flow.

**Cons:** Need to handle idempotency (`INSERT … ON CONFLICT DO NOTHING`) so the seed doesn't fail on restart.

**Context:**
- Backend: `src/harnex_api/db/models.py` — Tenant model
- Backend: `docker-compose.yml` or `src/harnex_api/main.py` — startup hooks
- Auth: `src/harnex_api/api/dependencies/auth.py` — `get_tenant_context()` accepts `X-Harnex-Dev-Tenant` in local/dev mode

**Depends on / blocked by:** Nothing.

---

## TODO 2: Return JSON-RPC error from MCP endpoint when unauthenticated

**What:** `src/harnex_api/mcp/server.py` — when the MCP tools/list or tools/call handler receives a request without a valid `Authorization: Bearer` token, return a proper JSON-RPC error response instead of an empty body.

**Why:** Currently `curl localhost:8000/mcp` returns an empty response. A developer trying to use the MCP surface gets dead silence with no clue that authentication is needed, no link to create a key, no error code. This is the first touchpoint for the actual product surface and it's a black hole.

**Pros:** Self-documenting endpoint. Developer knows exactly what to do: create an API key and pass it as a Bearer token. Follows the JSON-RPC error convention.

**Cons:** Needs a decision on whether to return the error for tools/list (which some MCP clients call pre-auth) vs tools/call (which should always require auth).

**Context:**
- `src/harnex_api/mcp/server.py` — `build_streamable_http_app()`, tool definitions
- `src/harnex_api/services/api_key_auth.py` — `authenticate_key()`

**Example response:**
```json
{"jsonrpc":"2.0","error":{"code":-32001,"message":"Authentication required. Create an API key at http://localhost:5173/api-keys and pass Authorization: Bearer hnx..."},"id":null}
```

**Depends on / blocked by:** TODO 1 (need a working API key to test with).

---

## TODO 3: Catch IntegrityError in POST handlers and return 400

**What:** Add a global exception handler or per-route try/except that catches `sqlalchemy.exc.IntegrityError` and returns a structured 400 error with the constraint name and a human-readable message.

**Why:** When the dev tenant FK check fails (or any future constraint violation), the raw SQLAlchemy exception propagates to FastAPI's default 500 handler. The user sees "Internal Server Error" with zero information. The real error is buried in docker logs. This happens for every POST/PUT/DELETE when the tenant isn't seeded, but it will also happen for duplicate key names, bad scope connection_ids, etc.

**Pros:** Every constraint violation returns a meaningful error. Developer can self-diagnose. Works for all future schema constraints automatically.

**Cons:** Must be careful not to leak internal schema details (table names, column names) in production errors. Condition on `HARNEX_ENV` or sanitize the message.

**Context:**
- `src/harnex_api/main.py` — FastAPI app, exception handlers
- `src/harnex_api/api/routes/api_keys.py`, `connections.py` — POST handlers

**Depends on / blocked by:** Nothing.

---

## TODO 4: Fix two persistent 404s on every console page load

**What:** Either implement `GET /v1/usage/current` or remove the frontend call that hits it. Also fix the second 404 (unknown resource) that fires on every page load.

**Why:** The browser console logs two 404 errors on EVERY page load. Developer sees red error lines that look like the site is broken. The `/v1/usage/current` endpoint returns 404 on the API side, and the frontend keeps calling it.

**Pros:** Clean console. No false-alarm errors that mask real issues.

**Cons:** If usage/current is planned for later, removing the call means re-adding it. Better to stub the endpoint returning `{"used":0,"limit":1000}`.

**Context:**
- Backend: `src/harnex_api/api/routes/usage.py` — may or may not have the endpoint
- Frontend: `web/src/routes/_app/dashboard.tsx` — usage query, likely via `useApi().getUsage()`

**Depends on / blocked by:** Nothing.

---

## TODO 5: Style the 404 page with navigation

**What:** `web/src/routes/__root.tsx` (or wherever the catch-all/not-found route is defined) — replace the bare "Not Found" text with a styled page showing the Harnex logo, a clear "Page not found" message, and a link back to the dashboard.

**Why:** Navigating to any unknown route shows "Not Found" in the browser's default serif font. No navigation, no branding, no way to get back except the browser back button.

**Pros:** One component. Handles all 404s. Standard pattern.

**Cons:** Low priority relative to the blockers above.

**Context:**
- `web/src/routes/__root.tsx` — likely has a `notFoundComponent` or catch-all

**Depends on / blocked by:** Nothing.
