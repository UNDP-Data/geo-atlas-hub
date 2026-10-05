#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> [1/4] Creating KinD Cluster..."
(
  cd "${ROOT_DIR}/cluster"
  ./create.sh
)

echo "==> [2/4] Starting Cloud Provider KinD & Gateway..."
(
  cd "${ROOT_DIR}/ingress/cloud-provider-kind"
  ./install.sh
)

echo "==> [3/4] Installing Cert-Manager & Certificates..."
(
  cd "${ROOT_DIR}/cert"
  ./install.sh
)

echo "==> [4/4] Installing OAuth & Auth Routes..."
(
  cd "${ROOT_DIR}/oauth"
  ./install.sh

)

echo "==> Installation complete! All services deployed."