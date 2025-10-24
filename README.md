# Portfolio Management — Developer Guide

This repository contains a full‑stack portfolio management app: a FastAPI backend and a React (Vite) frontend. This guide helps developers build, run, and troubleshoot the app in local development and with Docker.

- Backend: FastAPI (Python 3.10+)
- Frontend: React + Vite (Node 18+)
- Database: PostgreSQL 15 (Docker)

## Prerequisites
- macOS or Linux (dev-tested on macOS)
- Docker and Docker CLI
- Python 3.10+ and pip
- Node 18+ and npm
- Optional for price/company data features: yfinance, pandas, psycopg2-binary

## Key paths
- Startup script: start_app.sh
- Stop script: stop_app.sh
- Backend entrypoint: source_code/main.py
- DB connection manager: source_code/config/pg_db_conn_manager.py
- SQL view DDL: source_code/config/sql/create_view_transaction_full.sql
- Frontend source: src/
- Production build output (served by FastAPI): dist/

## How configuration works
- App environment is selected via CLI flag or env var, in order:
  1) --env <val> when starting the Python app
  2) APP_ENV environment variable
  3) Default: test
- main.py loads a .env file that matches the selected env: .env.<env> from either the repo root or alongside main.py, if present.
- Database env vars expected (e.g., when running without the helper script):
  - DB_HOST, DB_NAME, DB_USER, DB_PASS, DB_PORT
- Frontend base URL for API can be set at build time via VITE_API_BASE_URL (defaults to same origin in production, http://localhost:8000 during Vite dev).

## Quick start — local development
1) Backend
- Install dependencies:
  pip install -r requirements.txt
  # Optional extras for data features
  pip install psycopg2-binary pandas yfinance
- Run FastAPI with auto-reload:
  uvicorn source_code.main:app --reload

2) Frontend
- Install dependencies:
  npm install
- Run Vite dev server:
  npm run dev
- The frontend will call the API at http://localhost:8000 by default in dev.

## Quick start — Docker (recommended path)
The start_app.sh script manages a local Docker network, a PostgreSQL container, and the app container.

Make the script executable once:
- chmod +x start_app.sh stop_app.sh

Common invocations:
- ./start_app.sh --db-pass=YOUR_DB_PASS --env=qa
- ./start_app.sh --db-password YOUR_DB_PASS --app-env=prod
- ./start_app.sh  # prompts for DB password interactively (env defaults to qa)

Defaults and ports:
- Default environment is qa when not specified.
- QA host ports: Postgres 5431, FastAPI 8081 (container listens on 5432/8000).
- Prod host ports: Postgres 5430, FastAPI 8080 (container listens on 5432/8000).
- This allows running QA and Prod containers at the same time without port conflicts.

What it does:
- Creates docker network port_mgmt_net_<env> if needed
- Starts or creates a PostgreSQL 15 container mapped to the env-specific host port (5431 for QA, 5430 for Prod)
- Builds and runs the FastAPI app container mapped to the env-specific host port (8081 for QA, 8080 for Prod) while the app listens on 8000 in-container
- Prints container status at the end

To stop the stack:
- ./stop_app.sh --env=qa

## Build a production image
You can build the image directly or use the helper script.

- docker build -t munnydocker/port_mgmt-python-app-image .

Or use the enhanced build script with optional push support:

- ./build_app_image.sh
- IMAGE_TAG=latest ./build_app_image.sh
- REGISTRY=docker.io IMAGE_NAME=youruser/portfolio-mgmt IMAGE_TAG=latest \
  USERNAME=youruser PASSWORD=yourtoken DOCKER_PUSH=1 ./build_app_image.sh
- REGISTRY=ghcr.io IMAGE_NAME=yourorg/portfolio-mgmt IMAGE_TAG=latest \
  USERNAME=yourgithub GHCR_TOKEN=ghp_xxx DOCKER_PUSH=1 ./build_app_image.sh

Notes:
- If DOCKER_PUSH=1, the script tags the image as REGISTRY/IMAGE_NAME:IMAGE_TAG, logs in, and pushes.
- Ensure you have permission to push to the chosen registry/repository.

## Useful endpoints and app features
- Securities list: /securities (TopBar → Securities → List)
- Add multiple (manual table): /securities/new-bulk
- Import by tickers (YahooQuery): /securities/import
  - Frontend calls POST /api/securities/save_company_data_from_tickers with an array of tickers.
- Security Prices admin: TopBar → Portfolio Admin → Download Prices

## Manual Docker commands (advanced)
Create network and run Postgres (qa example):
- docker network create port_mgmt_net_qa  # if not created
- docker run -d \
    --name port_mgmt_postgres_qa \
    --network port_mgmt_net_qa \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=YOUR_DB_PASS \
    -e POSTGRES_DB=investment_db_qa \
    -v "/path/to/data/qa":/var/lib/postgresql/data \
    -v "/path/to/init-scripts/qa":/docker-entrypoint-initdb.d \
    -p 5431:5432 \
    postgres:15-alpine3.21

Run the app container against that DB:
- docker run -d \
    --name port_mgmt-python-app-container_qa \
    --network port_mgmt_net_qa \
    -e APP_ENV=qa \
    -e POSTGRES_DB_DB_HOST=port_mgmt_postgres_qa \
    -e POSTGRES_DB_DB_NAME=investment_db_qa \
    -e POSTGRES_DB_DB_USER=postgres \
    -e POSTGRES_DB_PASS="YOUR_DB_PASS" \
    -e POSTGRES_DB_DB_PORT=5432 \
    -p 8080:8000 \
    munnydocker/port_mgmt-python-app-image

Stop and remove:
- docker stop port_mgmt-python-app-container_qa port_mgmt_postgres_qa
- docker rm   port_mgmt-python-app-container_qa port_mgmt_postgres_qa
- docker network rm port_mgmt_net_qa
- docker rmi munnydocker/port_mgmt-python-app-image

## Troubleshooting
- Pushing image is denied
  - Ensure IMAGE_NAME includes your namespace (e.g., docker.io/youruser/repo:tag)
  - Verify the repository exists and you have write permissions
  - Use DOCKER_PUSH=1 with USERNAME and PASSWORD (or GHCR_TOKEN) in build_app_image.sh
- Blank page or 404 in production
  - Ensure the frontend is built into dist/ before starting the container
  - FastAPI serves dist/index.html for non-/api routes when dist exists
- CORS in dev
  - The backend allows all origins in dev; the frontend dev server targets http://localhost:8000
- DB connection errors
  - Check DB_* env vars (or use start_app.sh to pass them automatically)
  - Ensure the Postgres container is running and reachable on the Docker network

## Project structure (top level)
- source_code/        FastAPI app, routers, models, utils
- src/                React app (Vite)
- dist/               Production build output (created by npm run build)
- start_app.sh        Orchestrates local Docker stack
- stop_app.sh         Stops and removes containers (env-aware)
- build_app_image.sh  Build/tag/push helper for the app image
- Dockerfile          Multi-stage build for frontend+backend
- requirements.txt    Python dependencies
- package.json        Frontend scripts/deps
- tests/              Backend tests (if present)
