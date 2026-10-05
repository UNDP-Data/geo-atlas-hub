#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

if [ ! -f "${SCRIPT_DIR}/.env" ]; then
  echo "Error: Missing ${SCRIPT_DIR}/.env file." >&2
  exit 1
fi

# Load variables
# shellcheck source=/dev/null
set -a
source "${SCRIPT_DIR}/.env"
set +a

# Validate required variables
: "${CLOUDFLARE_API_TOKEN:?Environment variable CLOUDFLARE_API_TOKEN must be set}"
: "${ACME_EMAIL:?Environment variable ACME_EMAIL must be set}"
: "${BASE_DOMAIN:?Environment variable BASE_DOMAIN must be set}"

# Fallbacks for optional variables
export ACME_SERVER="${ACME_SERVER:-https://acme-v02.api.letsencrypt.org/directory}"
export CERT_NAMESPACE="${CERT_NAMESPACE:-default}"
export CERT_NAME="${CERT_NAME:-wildcard-${BASE_DOMAIN//./-}-cert}"
export CERT_SECRET_NAME="${CERT_SECRET_NAME:-wildcard-${BASE_DOMAIN//./-}-tls}"

echo "==> [cert] Adding Jetstack Helm repository..."
helm repo add jetstack https://charts.jetstack.io --force-update >/dev/null 2>&1
helm repo update jetstack

echo "==> [cert] Installing/Upgrading cert-manager..."
helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set crds.enabled=true \
  --set "extraArgs={--enable-gateway-api,--dns01-recursive-nameservers-only,--dns01-recursive-nameservers=1.1.1.1:53\,8.8.8.8:53}" \
  --wait \
  --timeout=2m

echo "==> [cert] Verifying webhook readiness..."
kubectl rollout status deployment/cert-manager-webhook -n cert-manager --timeout=60s

echo "==> [cert] Creating Cloudflare API Token Secret..."
kubectl create secret generic cloudflare-api-token \
  --namespace cert-manager \
  --from-literal=api-token="${CLOUDFLARE_API_TOKEN}" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "==> [cert] Applying ClusterIssuer for domain '${BASE_DOMAIN}'..."
envsubst < "${SCRIPT_DIR}/le-cluster-issuer.yaml" | kubectl apply -f -

echo "==> [cert] Applying Certificate '${CERT_NAME}' in namespace '${CERT_NAMESPACE}'..."
envsubst < "${SCRIPT_DIR}/cluster-wide-cert.yaml" | kubectl apply -f -

echo "==> [cert] Deployment initiated. Monitoring certificate order..."