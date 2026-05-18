# Contributing to Harnex

Welcome! The fastest way to contribute is adding a new **connector** — a small class that teaches Harnex how to discover and execute against a new API. This guide walks you from zero to a merged PR.

**Quick links**
- Connector contract → `src/harnex_api/connectors/base.py`
- Registry → `src/harnex_api/connectors/registry.py`
- Existing connectors → `src/harnex_api/connectors/` (github, slack, linear, jira, kubernetes, …)
- Issue templates → [open one to claim a connector](https://github.com/pranavvp16/harnex/issues/new?template=new_connector.yml)

---

## Table of contents

1. [Dev setup](#1-dev-setup)
2. [The connector contract](#2-the-connector-contract)
3. [Auth flows](#3-auth-flows)
4. [Override guide](#4-override-guide)
5. [Walkthrough: adding Stripe](#5-walkthrough-adding-stripe)
6. [Test requirements](#6-test-requirements)
7. [Style conventions](#7-style-conventions)
8. [PR process](#8-pr-process)
9. [Proposing a connector without implementing it](#9-proposing-without-implementing)

---

## 1. Dev setup

```bash
git clone https://github.com/pranavvp16/harnex && cd harnex
cp .env.example .env          # fill POSTGRES_PASSWORD + INFISICAL_ENCRYPTION_KEY (exactly 32 chars)
uv sync --extra dev           # install runtime + dev deps
```

Unit tests need **no running services**:

```bash
uv run pytest tests/unit      # fast, no Postgres / Infisical / OpenAI
```

For integration tests and running the full stack locally:

```bash
docker compose up -d postgres keycloak infisical
uv run alembic upgrade head
uv run uvicorn harnex_api.main:app --reload
```

Full quality gate (same as CI):

```bash
uv run ruff check .
uv run ruff format .
uv run mypy src
uv run pytest tests/unit
```

---

## 2. The connector contract

Every connector implements the `Connector` Protocol defined in `src/harnex_api/connectors/base.py`:

```python
class Connector(Protocol):
    key: ClassVar[str]                        # registry slug, e.g. "stripe"
    display_name: ClassVar[str]               # human label, e.g. "Stripe"
    supported_auth: ClassVar[list[AuthFlow]]  # auth methods this API accepts
    default_base_url: ClassVar[str | None]    # None = must be supplied per connection

    async def load_spec(self, connection: ConnectionConfig) -> LoadedSpec | None: ...
    async def infer_base_url(self, connection: ConnectionConfig, spec: LoadedSpec | None) -> str | None: ...
    async def build_auth_context(self, tenant_id, connection_id, auth_flow, auth_config) -> Any: ...
    async def before_execute(self, request: ExecuteRequest) -> ExecuteRequest: ...
```

**You never implement this Protocol directly.** Subclass `BaseConnector` — it provides production-ready defaults for all four methods. Override only what your connector needs to change.

```python
class BaseConnector:
    # load_spec       → returns None (no spec)
    # infer_base_url  → connection.base_url → spec servers[0] → default_base_url
    # build_auth_context → resolves secrets from Infisical + dispatches to AuthStrategy
    # before_execute  → identity (returns request unchanged)
```

**Do not override `build_auth_context`.** Secret resolution and auth injection are handled centrally; adding a new auth pattern means adding a new `AuthFlow` value and `AuthStrategy` — not overriding this method.

---

## 3. Auth flows

From `src/harnex_api/db/models.py::AuthFlow`:

| Value | When to use |
|---|---|
| `none` | Public API, no credentials |
| `bearer` | `Authorization: Bearer <token>` — API keys, JWTs, PATs |
| `basic` | HTTP Basic Auth — username + password or API token |
| `api_key_header` | Custom header name, e.g. `X-Api-Key: ...` |
| `api_key_query` | API key in query param, e.g. `?api_key=...` |
| `oauth_authcode` | OAuth 2.0 Authorization Code (user grants access) |
| `oauth_clientcred` | OAuth 2.0 Client Credentials (machine-to-machine) |

Set `supported_auth` to the flows the API actually supports — this drives the connection wizard in the console UI. Most APIs support more than one (e.g. GitHub: `bearer` + `oauth_authcode`).

---

## 4. Override guide

| Method | Override when | Example |
|---|---|---|
| `load_spec` | The API has a public OpenAPI spec URL | GitHub, Slack, Jira — fetch from CDN |
| `infer_base_url` | Base URL is tenant-specific | Jira: `return connection.base_url` only (never fall through to spec servers — their placeholder URLs break routing) |
| `before_execute` | Requests need transformation before the sandbox sends them | Linear: rewrite every call to `POST /graphql`; Kubernetes: add `Accept: application/json` |

See `src/harnex_api/connectors/linear.py` for a `before_execute` example, `src/harnex_api/connectors/jira.py` for an `infer_base_url` example, and `src/harnex_api/connectors/github.py` as the minimal happy-path template.

---

## 5. Walkthrough: adding Stripe

### Step 1 — Create `src/harnex_api/connectors/stripe.py`

```python
from __future__ import annotations

from typing import ClassVar

from harnex_api.connectors.base import (
    BaseConnector,
    ConnectionConfig,
    ConnectorTestEndpoint,
    LoadedSpec,
)
from harnex_api.db.models import AuthFlow

STRIPE_OPENAPI_URL = (
    "https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json"
)


class StripeConnector(BaseConnector):
    """Stripe API connector.

    Bearer token = Stripe API key (sk_live_... or sk_test_...).
    The default spec is Stripe's official OpenAPI description maintained at
    https://github.com/stripe/openapi; override via connection.spec_url if needed.
    """

    key: ClassVar[str] = "stripe"
    display_name: ClassVar[str] = "Stripe"
    supported_auth: ClassVar[list[AuthFlow]] = [AuthFlow.bearer]
    default_base_url: ClassVar[str | None] = "https://api.stripe.com"
    test_endpoint: ClassVar[ConnectorTestEndpoint] = ConnectorTestEndpoint(
        method="GET", path="/v1/account"
    )

    async def load_spec(self, connection: ConnectionConfig) -> LoadedSpec | None:
        from harnex_api.services.ingestion.fetcher import fetch_spec_from_url

        spec_url = connection.spec_url or STRIPE_OPENAPI_URL
        return await fetch_spec_from_url(spec_url)


__all__ = ["STRIPE_OPENAPI_URL", "StripeConnector"]
```

No `infer_base_url` or `before_execute` override — Stripe has a fixed base URL and no request transformation.

### Step 2 — Register in `src/harnex_api/connectors/registry.py`

Add to `register_builtins()`:

```python
from harnex_api.connectors import (
    ...,
    stripe,   # add this import
)

for cls in (
    ...,
    stripe.StripeConnector,   # add this entry
):
```

### Step 3 — Write tests

```bash
# Create tests/unit/connectors/test_stripe_connector.py
# See tests/unit/connectors/ for patterns
```

Minimum coverage for Stripe (which only overrides `load_spec`):
- Metadata: `key`, `display_name`, `default_base_url`, `test_endpoint`, `supported_auth`
- `load_spec` with `spec_url=None` → fetches `STRIPE_OPENAPI_URL`
- `load_spec` with custom `spec_url` → fetches that URL instead
- `infer_base_url` with no `connection.base_url` → returns `"https://api.stripe.com"` (inherited BaseConnector default)

Stub `harnex_api.services.ingestion.fetcher.fetch_spec_from_url` via `monkeypatch` — no live HTTP in tests.

### Step 4 — Verify

```bash
uv run ruff check .
uv run mypy src
uv run pytest tests/unit/connectors/ -v
```

---

## 6. Test requirements

Every connector PR **must** include `tests/unit/connectors/test_<key>_connector.py`.

**What to test:**

1. **Metadata** — `key`, `display_name`, `default_base_url`, `test_endpoint`, `supported_auth` values
2. **Every overridden method** — cover the override's specific behavior and its edge cases
3. **Inherited behavior still applies** — if you override `infer_base_url`, test that `connection.base_url` still wins when set

**Rules:**

- No live HTTP calls. Stub `fetch_spec_from_url` / `fetch_spec_for_connection` via `monkeypatch`:
  ```python
  import harnex_api.services.ingestion.fetcher as fetcher_mod
  monkeypatch.setattr(fetcher_mod, "fetch_spec_from_url", your_fake)
  ```
- Use `@pytest.mark.asyncio` for async tests (or rely on `asyncio_mode = auto` in `pyproject.toml`).
- Use the helpers from `tests/unit/connectors/conftest.py`:
  - `make_connection(connector_key=..., base_url=..., spec_url=...)` — builds a `ConnectionConfig`
  - `make_request(method=..., path=..., headers=..., body=...)` — builds an `ExecuteRequest`
- All tests must pass `uv run pytest tests/unit`.

The contract tests in `tests/unit/connectors/test_connector_contract.py` run automatically against every registered connector — they'll catch missing ClassVars and Protocol violations without any action on your part.

---

## 7. Style conventions

- `from __future__ import annotations` at the top of every new `.py` file
- `ClassVar[T]` annotation on every connector class variable (required for `mypy strict`)
- Line length 100 — enforced by `ruff`; selected rules: `E F I B UP N SIM RUF`
- Connector `key` must be lowercase ASCII; use hyphens for multi-word (e.g. `"google-sheets"`)
- Docstrings on the connector class (not the methods) — describe auth token format, notable behavior, and any quirks
- No `# noqa: B008` comments — FastAPI `Depends(...)` is the only intentional exception and is pre-configured

---

## 8. PR process

1. **Claim the issue** — Comment on the tracking issue (or open one with the [connector template](https://github.com/pranavvp16/harnex/issues/new?template=new_connector.yml)) before starting
2. **Branch name** — `connector/<key>` (e.g. `connector/stripe`)
3. **Open the PR** — Reference the tracking issue with `Closes #N`
4. **CI must be green** — `ruff check`, `mypy src`, `pytest tests/unit` all pass
5. **One approval** from a codeowner required before merge

---

## 9. Proposing without implementing

Not ready to write code? Open a [connector request issue](https://github.com/pranavvp16/harnex/issues/new?template=new_connector.yml) — fill in the API details (base URL, auth flows, OpenAPI spec URL, test endpoint) and someone else can pick it up. Good connector proposals come with a link to an official or well-maintained community OpenAPI spec.
