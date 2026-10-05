#!/bin/bash

# Determine the directory where this script resides
SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" >/dev/null 2>&1 && pwd)"

# Source the .env file relative to the script directory
. "$SCRIPT_DIR/.env"
echo "stopping KIND cluster $CLUSTER_NAME "
# Stop all containers belonging to the cluster
docker ps -q --filter "label=io.x-k8s.kind.cluster=${CLUSTER_NAME}" | xargs -r docker stop