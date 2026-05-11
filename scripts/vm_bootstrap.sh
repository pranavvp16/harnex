#!/usr/bin/env bash
# First-time setup for the Azure VM. Run once after `az vm create`:
#   ssh azureuser@<fqdn>
#   curl -fsSL <raw-url-to-this-script> | sudo bash
# Or, after cloning the repo:
#   sudo bash /opt/harnex/scripts/vm_bootstrap.sh
#
# Idempotent — safe to re-run.

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Run as root (sudo)." >&2
  exit 1
fi

VM_USER="${VM_USER:-azureuser}"
REPO_URL="${REPO_URL:-https://github.com/pranavvp16/harnex.git}"
REPO_DIR="${REPO_DIR:-/opt/harnex}"
DATA_DIR="${DATA_DIR:-/data}"

echo "==> Updating apt"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y --no-install-recommends \
  ca-certificates curl gnupg lsb-release git jq

# --- Docker -----------------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  echo "==> Installing Docker Engine + compose plugin"
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    >/etc/apt/sources.list.d/docker.list
  apt-get update -y
  apt-get install -y docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin
  systemctl enable --now docker
fi
usermod -aG docker "${VM_USER}"

# --- Azure CLI (used by deploy.sh for `az acr login --identity`) ------------
if ! command -v az >/dev/null 2>&1; then
  echo "==> Installing Azure CLI"
  curl -sL https://aka.ms/InstallAzureCLIDeb | bash
fi

# --- Data disk --------------------------------------------------------------
# Azure attaches the data disk as the next sd? device. Pick the largest unmounted
# disk that has no partition table.
DATA_DEV=""
for dev in /dev/sd{c,d,e,f}; do
  [[ -b "$dev" ]] || continue
  if ! lsblk -n -o MOUNTPOINT "$dev" | grep -q '/'; then
    DATA_DEV="$dev"
    break
  fi
done

if [[ -z "${DATA_DEV}" ]]; then
  echo "!! Couldn't auto-detect data disk. Mount it manually at ${DATA_DIR} and re-run."
  exit 1
fi

if ! blkid "${DATA_DEV}" >/dev/null 2>&1; then
  echo "==> Formatting ${DATA_DEV} as ext4"
  mkfs.ext4 -L harnex-data "${DATA_DEV}"
fi

mkdir -p "${DATA_DIR}"
DATA_UUID=$(blkid -s UUID -o value "${DATA_DEV}")
if ! grep -q "${DATA_UUID}" /etc/fstab; then
  echo "UUID=${DATA_UUID} ${DATA_DIR} ext4 defaults,nofail 0 2" >>/etc/fstab
fi
mount -a
echo "==> Data disk mounted at ${DATA_DIR}"

# --- /data subdirs (owned so non-root postgres/keycloak containers can write) -
# Postgres/Keycloak containers run as their own UIDs; on bind mounts we can't
# rely on docker to chown for us. Use 0700 with broad UIDs since the volume
# is on a private VM (no other tenants).
mkdir -p \
  "${DATA_DIR}/postgres" \
  "${DATA_DIR}/keycloak-db" \
  "${DATA_DIR}/infisical-db" \
  "${DATA_DIR}/caddy" \
  "${DATA_DIR}/caddy-config"

# Postgres official image runs as uid 999. The pgvector/pgvector and
# postgres:16-alpine images are both built from the same base — same uid.
chown -R 999:999 "${DATA_DIR}/postgres" "${DATA_DIR}/keycloak-db" "${DATA_DIR}/infisical-db"
chown -R "${VM_USER}:${VM_USER}" "${DATA_DIR}/caddy" "${DATA_DIR}/caddy-config"
chmod 700 "${DATA_DIR}/postgres" "${DATA_DIR}/keycloak-db" "${DATA_DIR}/infisical-db"

# --- Clone repo -------------------------------------------------------------
if [[ ! -d "${REPO_DIR}/.git" ]]; then
  echo "==> Cloning ${REPO_URL} into ${REPO_DIR}"
  git clone "${REPO_URL}" "${REPO_DIR}"
fi
chown -R "${VM_USER}:${VM_USER}" "${REPO_DIR}"

# --- Login to ACR using the VM's managed identity ---------------------------
# Pull is needed before the first `docker compose up`. We attempt this here
# but it will no-op if the identity is still propagating — the per-deploy
# script will retry.
if [[ -n "${ACR_NAME:-}" ]]; then
  sudo -u "${VM_USER}" bash -c "az login --identity || true"
  sudo -u "${VM_USER}" bash -c "az acr login --name ${ACR_NAME} || true"
fi

cat <<EOF

------------------------------------------------------------
VM bootstrap complete.

Next:
  1. scp .env <your-laptop>:${REPO_DIR}/.env       (filled from .env.prod.example)
  2. log out / log back in (docker group)
  3. cd ${REPO_DIR}
  4. docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
  5. Tunnel to Infisical (one-time admin setup):
       ssh -L 8090:infisical:8080 ${VM_USER}@<this-vm>
       open http://localhost:8090/admin/signup
  6. After filling INFISICAL_* in .env: docker compose restart api
------------------------------------------------------------
EOF
