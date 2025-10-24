#!/bin/bash
set -e  # Stop on any error

# === ARG PARSING (DB password + APP_ENV) ===
DB_PASSWORD_INPUT=""
APP_ENV="qa"  # default environment

while [[ $# -gt 0 ]]; do
  case "$1" in
    --db-pass|--db-password)
      if [[ -n "$2" && ! "$2" =~ ^-- ]]; then
        DB_PASSWORD_INPUT="$2"
        shift 2
      else
        echo "❌ Error: --db-pass requires a value"
        exit 1
      fi
      ;;
    --db-pass=*|--db-password=*)
      DB_PASSWORD_INPUT="${1#*=}"
      shift 1
      ;;
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

# Prompt for DB password if not provided
if [ -z "$DB_PASSWORD_INPUT" ]; then
  read -s -p "Enter DB admin password: " DB_PASSWORD_INPUT
  echo
fi
POSTGRES_DB_PASS="$DB_PASSWORD_INPUT"

# === CONFIG ===
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$PROJECT_DIR"
POSTGRES_CONTAINER=port_mgmt_postgres_$APP_ENV
PY_APP_CONTAINER=port_mgmt-python-app-container_$APP_ENV
POSTGRES_IMAGE=postgres:15-alpine3.21
PY_APP_IMAGE=munnydocker/port_mgmt-python-app-image
POSTGRES_DB_USER=postgres
POSTGRES_DB_NAME=investment_db_$APP_ENV
DATA_DIR="/Users/srini/Documents/database/postgresql/portfolio_management/$APP_ENV/data"
INIT_SCRIPTS_DIR="/Users/srini/Documents/database/postgresql/portfolio_management/$APP_ENV/init-scripts"
NETWORK_NAME=port_mgmt_net_$APP_ENV

# Select host ports based on environment (to allow QA and Prod to run simultaneously)
# QA defaults: Postgres 5431, FastAPI 8081
# Prod defaults: Postgres 5430, FastAPI 8080
# Other envs fall back to QA defaults unless overridden later
HOST_PG_PORT=5431
HOST_APP_PORT=8081
# macOS ships an older bash without ${var,,}; use a portable lowercase conversion
APP_ENV_LC=$(printf '%s' "$APP_ENV" | tr '[:upper:]' '[:lower:]')
if [[ "$APP_ENV_LC" == "prod" || "$APP_ENV_LC" == "production" ]]; then
  HOST_PG_PORT=5430
  HOST_APP_PORT=8080
elif [[ "$APP_ENV_LC" == "qa" ]]; then
  HOST_PG_PORT=5431
  HOST_APP_PORT=8081
fi

# === STEP 0: Go to project directory ===
cd "$PROJECT_DIR"
echo "📂 Working directory: $PROJECT_DIR"
echo "🌎 Using APP_ENV='$APP_ENV'"
echo "📡 Host ports => Postgres: $HOST_PG_PORT, FastAPI: $HOST_APP_PORT"

# === STEP 1: Ensure data & init folders exist ===
for dir in "$DATA_DIR" "$INIT_SCRIPTS_DIR"; do
  if [ ! -d "$dir" ]; then
    echo "📁 Creating folder: $dir"
    mkdir -p "$dir"
  else
    echo "✅ Folder exists: $dir"
  fi
done

# === STEP 2: Ensure Docker network exists ===
if [ -z "$(docker network ls --filter name=^${NETWORK_NAME}$ --format '{{.Name}}')" ]; then
  echo "🌐 Creating Docker network: $NETWORK_NAME"
  docker network create $NETWORK_NAME
else
  echo "✅ Docker network '$NETWORK_NAME' already exists."
fi

# === STEP 3: Start PostgreSQL (if not running) ===
if [ "$(docker ps -q -f name=^${POSTGRES_CONTAINER}$)" ]; then
  echo "🐘 PostgreSQL container '$POSTGRES_CONTAINER' is already running."
else
  if [ "$(docker ps -aq -f name=^${POSTGRES_CONTAINER}$)" ]; then
    echo "⚠️ Found stopped PostgreSQL container. Starting it..."
    docker start $POSTGRES_CONTAINER
  else
    echo "🐘 Starting new PostgreSQL container on host port $HOST_PG_PORT..."
    docker run -d \
      --name $POSTGRES_CONTAINER \
      --network $NETWORK_NAME \
      -e POSTGRES_USER=$POSTGRES_DB_USER \
      -e POSTGRES_PASSWORD=$POSTGRES_DB_PASS \
      -e POSTGRES_DB=$POSTGRES_DB_NAME \
      -v "$DATA_DIR":/var/lib/postgresql/data \
      -v "$INIT_SCRIPTS_DIR":/docker-entrypoint-initdb.d \
      -p ${HOST_PG_PORT}:5432 \
      $POSTGRES_IMAGE
  fi
fi


# === STEP 4: Wait for PostgreSQL to be ready ===
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker exec $POSTGRES_CONTAINER pg_isready -U $POSTGRES_DB_USER > /dev/null 2>&1; do
  sleep 1
done
echo "✅ PostgreSQL is ready."

# === STEP 5: Build and start Python app (if not running) ===
if [ "$(docker ps -q -f name=^${PY_APP_CONTAINER}$)" ]; then
  echo "🐍 Python app container '$PY_APP_CONTAINER' is already running."
else
  if [ "$(docker ps -aq -f name=^${PY_APP_CONTAINER}$)" ]; then
    echo "⚠️ Found stopped Python app container. Starting it..."
    docker start $PY_APP_CONTAINER
  else
    echo "🐍 Building Python app image (if not already built)..."
    docker build -t $PY_APP_IMAGE "$APP_DIR"

    echo "🚀 Starting new Python app container on host port $HOST_APP_PORT..."
    docker run -d \
      --name $PY_APP_CONTAINER \
      --network $NETWORK_NAME \
      -e APP_ENV=$APP_ENV \
      -e POSTGRES_DB_DB_HOST=$POSTGRES_CONTAINER \
      -e POSTGRES_DB_DB_NAME=$POSTGRES_DB_NAME \
      -e POSTGRES_DB_DB_USER=$POSTGRES_DB_USER \
      -e POSTGRES_DB_PASS="$POSTGRES_DB_PASS" \
      -e POSTGRES_DB_DB_PORT=5432 \
      -p ${HOST_APP_PORT}:8000 \
      $PY_APP_IMAGE
  fi
fi

# === STEP 6: Done ===
echo "🎉 All containers are up and running on network '$NETWORK_NAME'!"
docker ps
