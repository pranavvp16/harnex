# TODOS

## Done (code / repo hygiene)

- **MCP:** Replay drained ASGI body on successful API-key auth; wrap app lifespan with `session_manager.run()` on the singleton FastMCP instance (`server.py`, `main.py`).
- **SSRF:** Connection wizard probe resolves hosts and blocks non-public IPs; builtin tests pin connector default base URLs only (`connection_test.py`).
- **Executions:** Request/response summaries sanitize sensitive headers before JSONB persist (`runner.py`).
- **Rate limit:** Redis sliding window via Lua when `HARNEX_REDIS_URL` is set; in-memory deque fallback documented as dev-only (`rate_limit.py`, `docker-compose.yml`, `pyproject.toml`, `.env.example`).
- **Secrets file hygiene:** `.env.docker` added to `.gitignore` and removed from git tracking (`git rm --cached`). Local file unchanged.

## Manual — operator / security (TODO 1 remainder)

Rotating compromised Infisical keys and rewriting git history cannot be automated safely from here:

1. Generate new `INFISICAL_ENCRYPTION_KEY` (32 chars) and `INFISICAL_AUTH_SECRET`.
2. Update live `.env` / deployment secrets and re-encrypt or re-import vault data as required by Infisical.
3. Scrub `.env.docker` from history, e.g. `git filter-repo --invert-paths --path .env.docker` (or equivalent), then **force-push** and coordinate with anyone who cloned the old history.
