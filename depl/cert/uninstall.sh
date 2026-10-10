#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

if [ -f "${SCRIPT_DIR}/.env" ]; then
  # shellcheck source=/dev/null
  set -a
  source "${SCRIPT_DIR}/.env"
  set +a
fi

# ACME Server endpoint
if [ "${LE_ENV}" = "prod" ]; then
  ACME_SERVER="https://acme-v02.api.letsencrypt.org/directory"
else
  ACME_SERVER="https://acme-staging-v02.api.letsencrypt.org/directory"
fi

# Resource Names & Target Namespace

CERT_NAME="wildcard-${BASE_DOMAIN//./-}-cert"
CERT_SECRET_NAME="wildcard-${BASE_DOMAIN//./-}-tls"

echo "==> [cert] Removing Certificate resources..."
if [ -f "${SCRIPT_DIR}/cluster-wide-cert.yaml" ]; then
  envsubst < "${SCRIPT_DIR}/cluster-wide-cert.yaml" | kubectl delete -f - --ignore-not-found=true
fi

echo "==> [cert] Removing Let's Encrypt ClusterIssuer..."
if [ -f "${SCRIPT_DIR}/le-cluster-issuer.yaml" ]; then
  envsubst < "${SCRIPT_DIR}/le-cluster-issuer.yaml" | kubectl delete -f - --ignore-not-found=true
else
  kubectl delete clusterissuer letsencrypt --ignore-not-found=true
fi

echo "==> [cert] Removing Cloudflare Secret..."
kubectl delete secret cloudflare-api-token -n cert-manager --ignore-not-found=true

echo "==> [cert] Uninstalling cert-manager Helm release..."
helm uninstall cert-manager -n cert-manager 2>/dev/null || true

echo "==> [cert] Deleting cert-manager namespace..."
kubectl delete namespace cert-manager --ignore-not-found=true

echo "==> [cert] Deleting cert-manager CRDs..."
(kubectl get crd -o name 2>/dev/null | grep 'cert-manager.io' || true) | xargs -r kubectl delete --ignore-not-found=true

echo "==> [cert] Teardown complete."