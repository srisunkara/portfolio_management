#!/bin/bash
set -e  # Stop on any fatal error

APP_ENV="qa"  # default environment

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env|--app-env)
      if [[ -n "$2" && ! "$2" =~ ^-- ]]; then
        APP_ENV="$2"
        shift 2
      else
        echo "❌ Error: --env requires a value"
        exit 1
      fi
      ;;
    --env=*|--app-env=*)
      APP_ENV="${1#*=}"
      shift 1
      ;;
    *)
      echo "⚠️ Ignoring unknown argument: $1"
      shift 1
      ;;
  esac
done

# === CONFIG ===
POSTGRES_CONTAINER=port_mgmt_postgres_$APP_ENV
PY_APP_CONTAINER=port_mgmt-python-app-container_$APP_ENV
NETWORK_NAME=port_mgmt_net_$APP_ENV

echo "🛑 Stopping and removing containers..."

# Stop containers if they are running
if [ "$(docker ps -q -f name=^${PY_APP_CONTAINER}$)" ]; then
  docker stop $PY_APP_CONTAINER
fi
if [ "$(docker ps -q -f name=^${POSTGRES_CONTAINER}$)" ]; then
  docker stop $POSTGRES_CONTAINER
fi

# Remove containers if they exist
if [ "$(docker ps -aq -f name=^${PY_APP_CONTAINER}$)" ]; then
  docker rm $PY_APP_CONTAINER
fi
if [ "$(docker ps -aq -f name=^${POSTGRES_CONTAINER}$)" ]; then
  docker rm $POSTGRES_CONTAINER
fi

# Remove Docker network if it exists
if [ "$(docker network ls --filter name=^${NETWORK_NAME}$ --format '{{.Name}}')" ]; then
  echo "🌐 Removing Docker network: $NETWORK_NAME"
  docker network rm $NETWORK_NAME
else
  echo "✅ Docker network '$NETWORK_NAME' not found (nothing to remove)."
fi

echo "✅ All containers stopped and cleaned up successfully."
