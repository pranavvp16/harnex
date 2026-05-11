#!/usr/bin/env bash
# Run on the Azure VM by the GitHub Actions deploy workflow over SSH.
#
# Usage:   bash /opt/harnex/scripts/deploy.sh <git-sha>
# Effect:  pull the matching API + web images from ACR, restart the compose stack,
#          prune dangling images.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <image-tag>" >&2
  exit 2
fi

IMAGE_TAG="$1"
REPO_DIR="${REPO_DIR:-/opt/harnex}"
cd "${REPO_DIR}"

if [[ ! -f .env ]]; then
  echo "!! .env not found at ${REPO_DIR}/.env — populate it from .env.prod.example before deploying." >&2
  exit 1
fi

# Pick up ACR_NAME from .env so the script is self-contained.
# shellcheck disable=SC1091
set -a; . ./.env; set +a

: "${ACR_LOGIN_SERVER:?ACR_LOGIN_SERVER must be set in .env}"
ACR_NAME="${ACR_NAME:-${ACR_LOGIN_SERVER%%.*}}"

echo "==> Logging into ACR ${ACR_NAME} via VM managed identity"
az login --identity --only-show-errors >/dev/null
az acr login --name "${ACR_NAME}" --only-show-errors

export IMAGE_TAG
echo "==> Pulling images at tag ${IMAGE_TAG}"
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull api web

echo "==> Reconciling stack"
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --remove-orphans

echo "==> Pruning dangling images"
docker image prune -f

echo "==> Deploy ${IMAGE_TAG} done"
