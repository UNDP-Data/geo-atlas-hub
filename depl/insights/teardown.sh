#!/bin/bash

# Dynamically find the script's location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

echo "Tearing down Insights Hub resources..."

# Delete resources defined in the manifest safely
kubectl delete -f "$SCRIPT_DIR/insights-hub.yaml" --ignore-not-found=true

echo "Teardown complete!"