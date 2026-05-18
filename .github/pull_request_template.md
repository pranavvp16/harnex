## Summary

<!-- One sentence: what does this PR do? -->

Closes #<!-- issue number -->

## Type of change

- [ ] New connector (`connector/<key>`)
- [ ] Bug fix
- [ ] Feature / enhancement
- [ ] Refactor / chore
- [ ] Docs only

---

## Connector checklist

_Skip this section if this is not a connector PR._

- [ ] New file at `src/harnex_api/connectors/<key>.py` with `key`, `display_name`,
      `supported_auth`, `default_base_url`, and `test_endpoint` set as `ClassVar`s
- [ ] Registered in `register_builtins()` in `src/harnex_api/connectors/registry.py`
- [ ] `tests/unit/connectors/test_<key>_connector.py` covers all overridden methods
- [ ] Contract tests pass: `uv run pytest tests/unit/connectors/test_connector_contract.py -v`
- [ ] No live HTTP calls in tests (spec fetcher stubbed via `monkeypatch`)
- [ ] Class docstring describes auth token format and any notable behavior

---

## General checklist

- [ ] `uv run ruff check .` — no errors
- [ ] `uv run mypy src` — no errors
- [ ] `uv run pytest tests/unit` — all green
- [ ] `from __future__ import annotations` at the top of every new `.py` file
- [ ] `ClassVar[T]` annotations on all connector class variables
