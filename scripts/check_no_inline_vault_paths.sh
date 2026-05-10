#!/usr/bin/env bash
# Fail if any caller passes a string-literal path to the vault — every path
# must come from auth.vault.connection_secret_path / connector_token_path so
# the tenant_id segment is validated. Today the only callers are
# services/connections.py (via helper) and auth/vault.py itself; this guard
# stops future drift.
set -euo pipefail

# Match get_vault().{get,set,delete}_secret followed by a string literal.
# Excludes auth/vault.py (the helpers live there).
matches=$(
    grep -REn --include='*.py' \
        -e 'get_vault\(\)\.(get|set|delete)_secret\([[:space:]]*"' \
        -e "get_vault\(\)\.(get|set|delete)_secret\([[:space:]]*'" \
        --exclude-dir=__pycache__ \
        src/ \
    | grep -v 'src/harnex_api/auth/vault.py' \
    || true
)

if [ -n "$matches" ]; then
    echo "$matches"
    echo
    echo "ERROR: vault paths must come from connection_secret_path()/connector_token_path()." >&2
    echo "       Don't pass string literals to get_vault().{get,set,delete}_secret." >&2
    exit 1
fi
echo "OK: no inline vault paths."
