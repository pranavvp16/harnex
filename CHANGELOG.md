# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0.0] - 2026-05-08

### Added

- **API key scoping**: Keys can now restrict execution to specific connections (`scope.type = "connections"` with a list of `connection_ids`). New keys default to `scope.type = "all"`.
- **API key expiry**: Keys support optional expiration (`expires_in_days`, max 10 years). Expired keys are rejected at auth time.
- **Connection test probe**: Built-in connectors (`github`, `gitlab`, `jenkins`, `jira`, `kubernetes`, `linear`, `slack`) now expose a `test_endpoint` — `POST /v1/connections/test` runs a dry-run auth probe before the connection is saved.
- **Code-mode execution**: `execute_code()` runs a generated Node.js fetch script inside the Blaxel sandbox. Agents can request code mode via `ExecuteRequestIn(mode="code")`.
- **Sandbox pre-warm**: `create_app()` provisions the Blaxel sandbox on startup (idempotent). Failures are non-fatal.
- **New dashboard**: Replaced sparse KPI cards with a full dashboard showing connection health, recent executions, and usage quota bars.
- **Connections list redesign**: Filterable table with row selection, inline reindex/delete actions, and a delete confirmation modal.
- **Executions page redesign**: Searchable, filterable execution log with status filter and time range selector.
- **Usage page redesign**: Quota bars, KPI cards, and a 30-day execution sparkline.
- **Design system**: CSS variable-based design token system (`--ink`, `--surface`, `--accent`, etc.) with light and dark themes. Atmosphere background, grid overlay, CSS button/input/badge/table/alert primitives.

### Changed

- **Frontend migration**: Moved from Tailwind component classes to CSS custom properties. `globals.css` now owns all design primitives.
- **Landing redirect**: Anonymous users now go to `/home` instead of the blank `/`.
- **Executions API**: `GET /v1/executions` now returns a paginated `Page` object with `items` and `total` (was an array).
- **MCP execute**: Validates `connection_id` is a valid UUID before scope check. Returns structured error on scope violation.
- **`enricher.py`**: Fixed formatting — single-line conditionals for `operationId` and `security`.
- **Ruff**: Fixed unsorted import in `scripts/blaxel_provision.py`.

### Infrastructure

- CORS middleware added for `local`/`dev` environments (allows `localhost:PORT`).
- `BlaxelSandboxRunner.run_node_script` now builds the Node eval command with embedded base64 source.
- Added `generate_fetch_script()` helper for code-mode sandbox execution.