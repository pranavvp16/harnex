#!/usr/bin/env bash
# Patch the imported `harnex` realm with the production public hostname.
#
# Runs once after the first `docker compose up -d`. Uses `kcadm.sh` from inside
# the running keycloak container so no extra tooling is needed on the host.
#
# Required env (sourced from .env if present):
#   HARNEX_PUBLIC_HOST       e.g. harnex-app.eastus2.cloudapp.azure.com
#   KEYCLOAK_ADMIN           default: admin
#   KEYCLOAK_ADMIN_PASSWORD  from .env
#   KEYCLOAK_ADMIN_CLIENT_SECRET  optional; rotates harnex-admin-cli secret
#
# Idempotent.

set -euo pipefail

REPO_DIR="${REPO_DIR:-/opt/harnex}"
if [[ -f "${REPO_DIR}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; . "${REPO_DIR}/.env"; set +a
fi

: "${HARNEX_PUBLIC_HOST:?HARNEX_PUBLIC_HOST must be set}"
: "${KEYCLOAK_ADMIN_PASSWORD:?KEYCLOAK_ADMIN_PASSWORD must be set}"
REALM="${KEYCLOAK_REALM:-harnex}"
ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
PUBLIC_BASE="https://${HARNEX_PUBLIC_HOST}"

# Resolve the keycloak container regardless of the compose project prefix.
KC_CT=$(docker ps --filter "label=com.docker.compose.service=keycloak" \
  --format '{{.Names}}' | head -n1)
if [[ -z "${KC_CT}" ]]; then
  echo "!! keycloak container not running" >&2
  exit 1
fi

kcadm() { docker exec "${KC_CT}" /opt/keycloak/bin/kcadm.sh "$@"; }

echo "==> Logging into kcadm as ${ADMIN_USER}"
# Keycloak is fronted by Caddy at /auth, but inside the container the server
# listens on http://localhost:8080 with KC_HTTP_RELATIVE_PATH=/auth.
kcadm config credentials \
  --server "http://localhost:8080/auth" \
  --realm master --user "${ADMIN_USER}" \
  --password "${KEYCLOAK_ADMIN_PASSWORD}" >/dev/null

echo "==> Patching harnex-web client URLs"
WEB_ID=$(kcadm get clients -r "${REALM}" -q clientId=harnex-web --fields id \
  --format csv --noquotes | tail -n1)
if [[ -z "${WEB_ID}" ]]; then
  echo "!! harnex-web client not found in realm ${REALM}" >&2
  exit 1
fi

kcadm update "clients/${WEB_ID}" -r "${REALM}" \
  -s "rootUrl=${PUBLIC_BASE}" \
  -s "baseUrl=${PUBLIC_BASE}/" \
  -s "redirectUris=[\"${PUBLIC_BASE}/*\"]" \
  -s "webOrigins=[\"${PUBLIC_BASE}\"]" \
  -s 'attributes."post.logout.redirect.uris"='"${PUBLIC_BASE}/*"

echo "==> harnex-web updated"

if [[ -n "${KEYCLOAK_ADMIN_CLIENT_SECRET:-}" ]]; then
  echo "==> Rotating harnex-admin-cli secret"
  ADM_ID=$(kcadm get clients -r "${REALM}" -q clientId=harnex-admin-cli \
    --fields id --format csv --noquotes | tail -n1)
  if [[ -n "${ADM_ID}" ]]; then
    kcadm update "clients/${ADM_ID}" -r "${REALM}" \
      -s "secret=${KEYCLOAK_ADMIN_CLIENT_SECRET}"
    echo "==> harnex-admin-cli secret rotated — restart api so it picks up the new secret"
  fi
fi

echo "Done. SPA should now redirect through ${PUBLIC_BASE}/auth/realms/${REALM}/..."
