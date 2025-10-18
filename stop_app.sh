#!/bin/bash

POSTGRES_CONTAINER=my-postgres
PY_APP_CONTAINER=my-python-app

echo "🛑 Stopping and removing containers..."
docker stop $PY_APP_CONTAINER $POSTGRES_CONTAINER 2>/dev/null || true
docker rm $PY_APP_CONTAINER $POSTGRES_CONTAINER 2>/dev/null || true

echo "✅ All containers stopped and removed."
