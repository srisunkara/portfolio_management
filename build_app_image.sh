#!/bin/bash
set -euo pipefail

# build_app_image.sh — Build, optionally tag, login, and push the app image
# Usage examples:
#   ./build_app_image.sh                                # build local image only
#   IMAGE_TAG=latest ./build_app_image.sh               # set tag (default: latest)
#   REGISTRY=docker.io USERNAME=jdoe IMAGE_NAME=jdoe/portfolio-mgmt \
#     PASSWORD=*** DOCKER_PUSH=1 ./build_app_image.sh   # login and push to Docker Hub
#   REGISTRY=ghcr.io IMAGE_NAME=yourorg/portfolio-mgmt DOCKER_PUSH=1 \
#     GHCR_TOKEN=*** USERNAME=yourgithub ./build_app_image.sh
#
# Env vars supported:
#   IMAGE_NAME           Final image name without registry (default: port_mgmt-python-app-image)
#   IMAGE_TAG            Tag to use (default: latest)
#   REGISTRY             Registry host (e.g., docker.io, ghcr.io) — optional
#   USERNAME             Registry username/login — required if DOCKER_PUSH=1
#   PASSWORD             Registry password/token — required if DOCKER_PUSH=1 (or use GHCR_TOKEN)
#   GHCR_TOKEN           Alternative to PASSWORD for ghcr.io
#   DOCKER_PUSH          If set to 1, will tag, login (if needed), and push
#   VITE_API_BASE_URL    Passed as Docker build ARG to set frontend API base
#   APP_ENV              Passed as Docker build ARG to set backend env (default test)

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$PROJECT_DIR"
LOCAL_IMAGE_NAME=${IMAGE_NAME:-munnydocker/port_mgmt-python-app-image}
IMAGE_TAG=${IMAGE_TAG:-latest}
APP_ENV_ARG=${APP_ENV:-test}
REGISTRY_HOST=${REGISTRY:-docker.io}
USERNAME=${USERNAME:-}
PASSWORD=${PASSWORD:-${GHCR_TOKEN:-}}
DOCKER_PUSH=${DOCKER_PUSH:-0}

cd "$PROJECT_DIR"
echo "📂 Working directory: $PROJECT_DIR"

# Build image
BUILD_ARGS=(
  "--build-arg" "APP_ENV=$APP_ENV_ARG"
)
if [[ -n "${VITE_API_BASE_URL:-}" ]]; then
  BUILD_ARGS+=("--build-arg" "VITE_API_BASE_URL=$VITE_API_BASE_URL")
fi

echo "🐍 Building app Docker image..."
docker build "${BUILD_ARGS[@]}" -t "$LOCAL_IMAGE_NAME:$IMAGE_TAG" "$APP_DIR"

echo "✅ Built local image: $LOCAL_IMAGE_NAME:$IMAGE_TAG"
echo "DOCKER_PUSH: $DOCKER_PUSH"
echo "IMAGE_TAG: $IMAGE_TAG"
echo "REGISTRY_HOST: $REGISTRY_HOST"

# When pushing, compute full name and tag appropriately
if [[ "$DOCKER_PUSH" == "1" ]]; then
  if [[ -z "$REGISTRY_HOST" ]]; then
    echo "⚠️ DOCKER_PUSH=1 but REGISTRY is not set. Set REGISTRY (e.g., docker.io) and IMAGE_NAME."
    exit 2
  fi
  if [[ -z "$USERNAME" || -z "$PASSWORD" ]]; then
    echo "⚠️ DOCKER_PUSH=1 but USERNAME or PASSWORD is missing. Provide credentials via USERNAME and PASSWORD (or GHCR_TOKEN)."
    exit 2
  fi

  FULL_IMAGE="$REGISTRY_HOST/$LOCAL_IMAGE_NAME:$IMAGE_TAG"
  echo "🔖 Tagging image as: $FULL_IMAGE"
  docker tag "$LOCAL_IMAGE_NAME:$IMAGE_TAG" "$FULL_IMAGE"

  echo "🔑 Logging in to $REGISTRY_HOST as $USERNAME ..."
  echo "$PASSWORD" | docker login "$REGISTRY_HOST" -u "$USERNAME" --password-stdin

  echo "📤 Pushing image: $FULL_IMAGE"
  if docker push "$FULL_IMAGE"; then
    echo "🎉 Push complete: $FULL_IMAGE"
  else
    echo "❌ Push failed. Common reasons:"
    echo "   - The repository '$REGISTRY_HOST/$LOCAL_IMAGE_NAME' does not exist or you lack permissions."
    echo "   - You are not allowed to push to that namespace (e.g., missing org membership)."
    echo "   - Wrong credentials or expired token."
    echo "👉 Fix: Ensure the repo exists and you have write access, then re-run with correct REGISTRY/IMAGE_NAME/USERNAME/PASSWORD."
    exit 3
  fi
fi

docker images | head -n 20
