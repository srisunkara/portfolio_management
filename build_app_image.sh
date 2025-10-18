#!/bin/bash
set -e  # Stop on any error

# === CONFIG ===
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$PROJECT_DIR"
PY_APP_IMAGE=port_mgmt-python-app-image

# === STEP 0: Go to project directory ===
cd "$PROJECT_DIR"
echo "📂 Working directory set to: $PROJECT_DIR"

# === STEP 1: Ensure data directory exists ===
    echo "🐍 Building Python app image (if not already built)..."
    docker build -t $PY_APP_IMAGE "$APP_DIR"

# === STEP 5: Done ===
echo "🎉 Docker build is complete - Image $PY_APP_IMAGE is built!"
docker ps
