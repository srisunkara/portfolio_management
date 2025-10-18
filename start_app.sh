#!/bin/bash
set -e  # Stop on any error

# === CONFIG ===
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$PROJECT_DIR"
POSTGRES_CONTAINER=port_mgmt_postgres
PY_APP_CONTAINER=port_mgmt-python-app-container
POSTGRES_IMAGE=postgres:15-alpine3.21
PY_APP_IMAGE=port_mgmt-python-app-image
POSTGRES_DB_ADMIN_USER=postgres
POSTGRES_DB_NAME=investment_db
DATA_DIR="/Users/srini/Documents/database/postgresql/portfolio_management/data"
INIT_SCRIPTS_DIR="/Users/srini/Documents/database/postgresql/portfolio_management/init-scripts"

# === ARG PARSING (DB password) ===
DB_PASSWORD_INPUT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --db-pass|--db-password)
      DB_PASSWORD_INPUT="$2"; shift 2;;
    --db-pass=*|--db-password=*)
      DB_PASSWORD_INPUT="${1#*=}"; shift 1;;
    *)
      shift 1;;
  esac
done

if [ -z "$DB_PASSWORD_INPUT" ]; then
  # Prompt user (hidden input) if not provided
  read -s -p "Enter DB admin password: " DB_PASSWORD_INPUT
  echo
fi

# Set password variable
POSTGRES_DB_ADMIN_PASSWORD="$DB_PASSWORD_INPUT"

# === STEP 0: Go to project directory ===
cd "$PROJECT_DIR"
echo "📂 Working directory set to: $PROJECT_DIR"

# === STEP 1: Ensure data directory exists ===
if [ ! -d "$DATA_DIR" ]; then
  echo "📁 Data folder not found. Creating: $DATA_DIR"
  mkdir -p "$DATA_DIR"
else
  echo "✅ Data folder already exists: $DATA_DIR"
fi

if [ ! -d "$INIT_SCRIPTS_DIR" ]; then
  echo "📁 Initial scripts folder not found. Creating: $INIT_SCRIPTS_DIR"
  mkdir -p "$INIT_SCRIPTS_DIR"
else
  echo "✅ Initial scripts folder already exists: $INIT_SCRIPTS_DIR"
fi

# === STEP 2: Start PostgreSQL (if not running) ===
if [ "$(docker ps -q -f name=^${POSTGRES_CONTAINER}$)" ]; then
  echo "🐘 PostgreSQL container '$POSTGRES_CONTAINER' is already running."
else
  if [ "$(docker ps -aq -f name=^${POSTGRES_CONTAINER}$)" ]; then
    echo "⚠️ Existing PostgreSQL container found (stopped). Starting it..."
    docker start $POSTGRES_CONTAINER
  else
    echo "🐘 Starting new PostgreSQL container..."
    docker run -d \
      --name $POSTGRES_CONTAINER \
      -e POSTGRES_USER=$POSTGRES_DB_ADMIN_USER \
      -e POSTGRES_PASSWORD=$POSTGRES_DB_ADMIN_PASSWORD \
      -e POSTGRES_DB=$POSTGRES_DB_NAME \
      -v "$DATA_DIR":/var/lib/postgresql/data \
      -v "$INIT_SCRIPTS_DIR":/docker-entrypoint-initdb.d \
      -p 5431:5432 \
      $POSTGRES_IMAGE
  fi
fi

# === STEP 3: Wait for PostgreSQL to be ready ===
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker exec $POSTGRES_CONTAINER pg_isready -U $POSTGRES_DB_ADMIN_USER > /dev/null 2>&1; do
  sleep 1
done
echo "✅ PostgreSQL is ready."

# === STEP 4: Build and start Python app (if not running) ===
if [ "$(docker ps -q -f name=^${PY_APP_CONTAINER}$)" ]; then
  echo "🐍 Python app container '$PY_APP_CONTAINER' is already running."
else
  if [ "$(docker ps -aq -f name=^${PY_APP_CONTAINER}$)" ]; then
    echo "⚠️ Existing Python app container found (stopped). Starting it..."
    docker start $PY_APP_CONTAINER
  else
    echo "🐍 Building Python app image (if not already built)..."
    docker build -t $PY_APP_IMAGE "$APP_DIR"

    echo "🚀 Starting new Python app container..."
    docker run -d \
      --name $PY_APP_CONTAINER \
      --link $POSTGRES_CONTAINER:postgres \
      -e DB_HOST=postgres \
      -e DB_NAME=$POSTGRES_DB_NAME \
      -e DB_USER=$POSTGRES_DB_ADMIN_USER \
      -e DB_PASS="$POSTGRES_DB_ADMIN_PASSWORD" \
      -e DB_PORT=5432 \
      -p 8080:8000 \
      $PY_APP_IMAGE
  fi
fi

# === STEP 5: Done ===
echo "🎉 All containers are up and running!"
docker ps
