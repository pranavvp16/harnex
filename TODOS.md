# TODOS

Working backlog: add new items under **Open** with severity + owner context. When done, move a one-line summary to **Completed** (keep history short).

---

## Open

### TODO 11 | HIGH | MCPAuthenticated Requests Return 500

**Files:** `src/harnex_api/mcp/server.py` line 237, `src/harnex_api/main.py` line 56/173

**What:** `POST /mcp/` with a valid `Authorization: Bearer hnx...` key returns HTTP 500. The MCP no-auth path works correctly (returns JSON-RPC `-32001` error), but once auth passes, the underlying FastMCP streamable HTTP app crashes.

**Root cause:** `FastMCP.streamable_http_app()` creates a Starlette ASGI app with a `session_manager` that requires an ASGI lifespan event to initialize its task group. When mounted via `app.mount("/mcp", build_streamable_http_app())`, FastAPI doesn't trigger the sub-app's lifespan, so the task group is never initialized. Result: `RuntimeError: Task group is not initialized. Make sure to use run().`

**Docker logs:**
```
mcp/server/fastmcp/server.py:1095 → session_manager.handle_request
mcp/server/streamable_http_manager.py:156 → RuntimeError: Task group is not initialized. Make sure to use run().
```

**Repro:**
1. Create an API key via the console
2. `curl -s -X POST http://localhost:8000/mcp/ -H "Authorization: Bearer hnx..." -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'`
3. Returns 500 Internal Server Error

**Fix options:**
- **A (recommended):** Call `await mcp_server.session_manager.run()` in the FastAPI `lifespan()` function, after dev tenant seed. Requires making the MCP app instance accessible in the lifespan scope (e.g., create it as a module-level singleton and import it).
- **B:** Use FastMCP's `sse_app()` transport instead of `streamable_http_app()` (SSE transport is more mature but deprecated in MCP spec v2).
- **C:** Mount the MCP app under a sub-path that includes its own lifespan handling via Starlette's Router.

**Additional note:** The auth middleware in `build_streamable_http_app()` creates a Starlette `Request` object to extract the Bearer token, which consumes the ASGI `receive` channel. When auth fails, this is fine (body is drained and discarded). When auth succeeds, the middleware forwards `scope, receive, send` to `inner`, but `receive` has already been consumed by `Request`. Fix this alongside the lifespan issue — either extract the Bearer from `scope["headers"]` directly, or drain+replay the body.

---

### TODO 12 | MEDIUM | Revocation Confirmation Renders Inline Instead of Modal

**Files:** `web/src/routes/_app/api-keys.tsx` lines 425-432

**What:** Clicking "Revoke" on an API key row shows the confirmation dialog inline below the row rather than as a centered modal overlay with backdrop. The standard pattern for destructive actions is a modal dialog. The code has a `<Modal>` component and `confirmRevoke` state, but the modal renders inline.

**Fix:** Ensure the `<Modal>` component uses a React portal or overlay wrapper to render centered. Check that `open={confirmRevoke !== null}` is being passed correctly and that `Modal` renders through a portal.

---

### TODO 13 | LOW | Dashboard Shows Positive Deltas on Zero Data

**Files:** `web/src/routes/_app/dashboard.tsx`

**What:** Dashboard shows "+2 this week" next to "Connections 0 — none yet" and "+18% vs last" next to "Executions 0 this month". These positive deltas on zero data are misleading.

**Fix:** When the count is 0, suppress the delta metric or show "—" instead of a fake positive number.

---

## Completed — `/devex-review` (2026-05-07)

- **TODO 1:** Seed dev tenant on first startup → `services/tenant/seed.py`; called from `main.py` lifespan
- **TODO 2:** JSON-RPC auth error from MCP → `mcp/server.py` middleware; `-32001` + 401 + `WWW-Authenticate`
- **TODO 3:** Catch IntegrityError → 400 → `main.py` global exception handler
- **TODO 4:** Fix persistent 404s → stubbed `/v1/usage/current`; dashboard query removed
- **TODO 5:** Style the 404 page → `__root.tsx` `notFoundComponent` with logo + dashboard link

---

## Completed — `/qa` (2026-05-09)

- **TODO 6:** Docker Compose stability (`docker-compose.yml`) — `restart: unless-stopped` on services; API `healthcheck`; `web` `depends_on: api` with `condition: service_healthy`.
- **TODO 7:** Vite first-run dev tenant — `web/.env.development` + `web/.env.example`; default API base empty (same-origin `/v1` + proxy in `vite.config.ts`).
- **TODO 8:** API key “Failed to fetch” / wrong URLs — fixed `env.apiUrl` default so paths `/v1/...` are not doubled (`web/src/lib/env.ts`).
- **TODO 9:** MCP `/mcp` vs `/mcp/` — `FastMCP(..., streamable_http_path="/")`; `307` redirect bare `/mcp` → `/mcp/` (`src/harnex_api/mcp/server.py`, `main.py`); `tests/integration/test_mcp_smoke.py`.
- **TODO 10:** ARIA landmarks — skip link + `role="navigation"` / `role="banner"` / `<main id="main-content">` (`web/src/routes/_app.tsx`, `web/src/styles/globals.css`).
