#!/bin/bash

# Determine the directory where this script resides
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Source the .env file relative to the script directory
. "$SCRIPT_DIR/.env"
echo "Deleting KIND cluster: $CLUSTER_NAME..."
kind delete cluster --name $CLUSTER_NAME
