#!/usr/bin/env bash
# One-time Azure provisioning for the Harnex single-VM deployment.
#
# Creates: resource group, public IP with DNS label, NSG with 22/80/443 rules,
# Ubuntu VM, attached data disk, ACR, a user-assigned managed identity for
# GitHub Actions (federated OIDC, no static secrets), and a system-assigned
# identity on the VM with AcrPull so the VM can pull images via `az acr login`.
#
# Prereqs:
#   - az cli logged in (`az login`) into the target subscription
#   - GH_REPO env var set to "<owner>/<repo>" so the federated credential
#     can be scoped correctly
#
# Idempotency: each `az ... create` is wrapped so re-runs are safe.

set -euo pipefail

: "${GH_REPO:?Set GH_REPO=<owner>/<repo> before running (e.g. pranavvp16/harnex)}"

# --- Knobs ------------------------------------------------------------------
LOCATION="${LOCATION:-eastus2}"
RG="${RG:-harnex-rg}"
VM_NAME="${VM_NAME:-harnex-vm}"
VM_SIZE="${VM_SIZE:-Standard_D4s_v5}"
VM_IMAGE="${VM_IMAGE:-Ubuntu2204}"
VM_USER="${VM_USER:-azureuser}"
OS_DISK_GB="${OS_DISK_GB:-64}"
DATA_DISK_GB="${DATA_DISK_GB:-64}"

PUBLIC_IP_NAME="${PUBLIC_IP_NAME:-harnex-ip}"
DNS_LABEL="${DNS_LABEL:-harnex-app}"          # final FQDN: ${DNS_LABEL}.${LOCATION}.cloudapp.azure.com
NSG_NAME="${NSG_NAME:-harnex-nsg}"

ACR_NAME="${ACR_NAME:-harnexacr}"             # must be globally unique, 5-50 alphanumeric
ACR_SKU="${ACR_SKU:-Basic}"

GH_IDENTITY_NAME="${GH_IDENTITY_NAME:-harnex-gh-deploy}"
SSH_KEY_PATH="${SSH_KEY_PATH:-$HOME/.ssh/harnex_azure_ed25519}"

echo "==> Subscription: $(az account show --query name -o tsv)"
echo "==> Location:     ${LOCATION}"
echo "==> RG:           ${RG}"

# --- SSH key ----------------------------------------------------------------
if [[ ! -f "${SSH_KEY_PATH}" ]]; then
  echo "==> Generating dedicated SSH key at ${SSH_KEY_PATH}"
  ssh-keygen -t ed25519 -f "${SSH_KEY_PATH}" -N "" -C "harnex-azure"
else
  echo "==> Reusing existing SSH key at ${SSH_KEY_PATH}"
fi

# --- Resource group ---------------------------------------------------------
az group create -n "${RG}" -l "${LOCATION}" -o none
echo "==> RG ready: ${RG}"

# --- Public IP + DNS label --------------------------------------------------
az network public-ip create \
  -g "${RG}" -n "${PUBLIC_IP_NAME}" \
  --sku Standard --allocation-method Static \
  --dns-name "${DNS_LABEL}" -o none
FQDN=$(az network public-ip show -g "${RG}" -n "${PUBLIC_IP_NAME}" \
  --query dnsSettings.fqdn -o tsv)
PUBLIC_IP=$(az network public-ip show -g "${RG}" -n "${PUBLIC_IP_NAME}" \
  --query ipAddress -o tsv)
echo "==> Public IP:    ${PUBLIC_IP}"
echo "==> Public FQDN:  ${FQDN}"

# --- NSG --------------------------------------------------------------------
az network nsg create -g "${RG}" -n "${NSG_NAME}" -o none

# Restrict SSH to the operator's current public IP if we can detect it.
MY_IP=$(curl -fsS https://api.ipify.org || echo "")
SSH_SOURCE="${MY_IP:+${MY_IP}/32}"
SSH_SOURCE="${SSH_SOURCE:-*}"

az network nsg rule create -g "${RG}" --nsg-name "${NSG_NAME}" \
  -n allow-ssh --priority 100 --direction Inbound \
  --source-address-prefixes "${SSH_SOURCE}" \
  --destination-port-ranges 22 --protocol Tcp --access Allow -o none || true

az network nsg rule create -g "${RG}" --nsg-name "${NSG_NAME}" \
  -n allow-http --priority 110 --direction Inbound \
  --source-address-prefixes '*' --destination-port-ranges 80 \
  --protocol Tcp --access Allow -o none || true

az network nsg rule create -g "${RG}" --nsg-name "${NSG_NAME}" \
  -n allow-https --priority 120 --direction Inbound \
  --source-address-prefixes '*' --destination-port-ranges 443 \
  --protocol Tcp --access Allow -o none || true

# --- VM ---------------------------------------------------------------------
if ! az vm show -g "${RG}" -n "${VM_NAME}" -o none 2>/dev/null; then
  az vm create \
    -g "${RG}" -n "${VM_NAME}" \
    --image "${VM_IMAGE}" --size "${VM_SIZE}" \
    --admin-username "${VM_USER}" \
    --ssh-key-values "${SSH_KEY_PATH}.pub" \
    --public-ip-address "${PUBLIC_IP_NAME}" \
    --nsg "${NSG_NAME}" \
    --os-disk-size-gb "${OS_DISK_GB}" \
    --storage-sku Premium_LRS \
    --assign-identity \
    -o none
  echo "==> VM created: ${VM_NAME}"
else
  echo "==> VM already exists: ${VM_NAME}"
fi

# Data disk for /data (Postgres, Keycloak DB, Infisical DB, Caddy certs)
if ! az disk show -g "${RG}" -n harnex-data -o none 2>/dev/null; then
  az vm disk attach -g "${RG}" --vm-name "${VM_NAME}" \
    --name harnex-data --size-gb "${DATA_DISK_GB}" \
    --sku Premium_LRS --new -o none
  echo "==> Data disk attached: harnex-data (${DATA_DISK_GB} GiB)"
else
  echo "==> Data disk already attached"
fi

# --- ACR --------------------------------------------------------------------
if ! az acr show -n "${ACR_NAME}" -o none 2>/dev/null; then
  az acr create -g "${RG}" -n "${ACR_NAME}" --sku "${ACR_SKU}" -o none
fi
ACR_LOGIN_SERVER=$(az acr show -n "${ACR_NAME}" --query loginServer -o tsv)
ACR_ID=$(az acr show -n "${ACR_NAME}" --query id -o tsv)
echo "==> ACR:          ${ACR_LOGIN_SERVER}"

# Grant the VM's system-assigned identity AcrPull so it can `az acr login --identity`.
VM_IDENTITY_PRINCIPAL=$(az vm show -g "${RG}" -n "${VM_NAME}" \
  --query identity.principalId -o tsv)
if [[ -n "${VM_IDENTITY_PRINCIPAL}" ]]; then
  az role assignment create \
    --assignee-object-id "${VM_IDENTITY_PRINCIPAL}" \
    --assignee-principal-type ServicePrincipal \
    --role AcrPull --scope "${ACR_ID}" -o none 2>/dev/null || true
  echo "==> VM identity granted AcrPull on ${ACR_NAME}"
fi

# --- GitHub Actions federated identity (OIDC) -------------------------------
SUB_ID=$(az account show --query id -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

if ! az identity show -g "${RG}" -n "${GH_IDENTITY_NAME}" -o none 2>/dev/null; then
  az identity create -g "${RG}" -n "${GH_IDENTITY_NAME}" -o none
fi
GH_CLIENT_ID=$(az identity show -g "${RG}" -n "${GH_IDENTITY_NAME}" --query clientId -o tsv)
GH_PRINCIPAL_ID=$(az identity show -g "${RG}" -n "${GH_IDENTITY_NAME}" --query principalId -o tsv)

# Grant AcrPush so GH Actions can push images.
az role assignment create \
  --assignee-object-id "${GH_PRINCIPAL_ID}" \
  --assignee-principal-type ServicePrincipal \
  --role AcrPush --scope "${ACR_ID}" -o none 2>/dev/null || true

# Federated credential — trust GitHub's OIDC issuer for pushes from `main`.
# (PR builds don't need it; the deploy workflow only fires on main.)
az identity federated-credential create -g "${RG}" \
  --identity-name "${GH_IDENTITY_NAME}" \
  --name harnex-gh-main \
  --issuer "https://token.actions.githubusercontent.com" \
  --subject "repo:${GH_REPO}:ref:refs/heads/main" \
  --audiences "api://AzureADTokenExchange" -o none 2>/dev/null || true

echo "==> GH OIDC identity ready: clientId=${GH_CLIENT_ID}"

# --- Summary ----------------------------------------------------------------
cat <<EOF

------------------------------------------------------------
Provisioning complete. Set these GitHub repo secrets:

  AZURE_CLIENT_ID         = ${GH_CLIENT_ID}
  AZURE_TENANT_ID         = ${TENANT_ID}
  AZURE_SUBSCRIPTION_ID   = ${SUB_ID}
  ACR_LOGIN_SERVER        = ${ACR_LOGIN_SERVER}
  ACR_NAME                = ${ACR_NAME}
  HARNEX_PUBLIC_HOST      = ${FQDN}
  VM_SSH_HOST             = ${FQDN}
  VM_SSH_USER             = ${VM_USER}
  VM_SSH_PRIVATE_KEY      = (paste contents of ${SSH_KEY_PATH})

Next steps:
  1. ssh -i ${SSH_KEY_PATH} ${VM_USER}@${FQDN}
  2. sudo bash /opt/harnex/scripts/vm_bootstrap.sh   # after cloning the repo
  3. Copy a filled-out .env (from .env.prod.example) to /opt/harnex/.env
  4. cd /opt/harnex && docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
  5. Push to main → GH Actions deploys
------------------------------------------------------------
EOF
