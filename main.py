# main.py
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables based on program parameter "env"
# Priority: CLI --env | --env=<val> > env var APP_ENV > default "test"
def _get_cli_env(argv: list[str]) -> str | None:
    try:
        if "--env" in argv:
            idx = argv.index("--env")
            if idx + 1 < len(argv):
                return argv[idx + 1]
        for arg in argv:
            if arg.startswith("--env="):
                return arg.split("=", 1)[1]
    except Exception:
        return None
    return None

# Accept DB password via CLI: --db-pass <val> or --db-password=<val>
def _get_cli_db_pass(argv: list[str]) -> str | None:
    try:
        # Support both spaced and equals forms
        if "--db-pass" in argv:
            idx = argv.index("--db-pass")
            if idx + 1 < len(argv):
                return argv[idx + 1]
        if "--db-password" in argv:
            idx = argv.index("--db-password")
            if idx + 1 < len(argv):
                return argv[idx + 1]
        for arg in argv:
            if arg.startswith("--db-pass="):
                return arg.split("=", 1)[1]
            if arg.startswith("--db-password="):
                return arg.split("=", 1)[1]
    except Exception:
        return None
    return None

_SELECTED_ENV = _get_cli_env(sys.argv) or os.environ.get("APP_ENV") or "test"
_ENV_FILE_NAME = f".env.{_SELECTED_ENV}".lower()
_APP_DIR = Path(__file__).resolve().parent
_CWD_DIR = Path.cwd()

# Look for the env file in both the current working directory and the app directory
_candidates = [
    _CWD_DIR / _ENV_FILE_NAME,
    _APP_DIR / _ENV_FILE_NAME,
]
_env_path = next((p for p in _candidates if p.is_file()), None)

# Fallback to test if selected file doesn't exist
if _env_path is None:
    print("[main] Env file not found for selected env; falling back to test")
    _SELECTED_ENV = "test"
    _ENV_FILE_NAME = ".env.test"
    _candidates = [
        _CWD_DIR / _ENV_FILE_NAME,
        _APP_DIR / _ENV_FILE_NAME,
    ]
    _env_path = next((p for p in _candidates if p.is_file()), None)

# Diagnostics about resolution
try:
    print("[main] Selected env:", _SELECTED_ENV)
    print("[main] Env search candidates:", ", ".join(str(p) for p in _candidates))
    if _env_path:
        print(f"[main] Using env file: {_env_path}")
    else:
        print("[main] No .env file found; proceeding without file load")
except Exception:
    pass

# Load the environment file (does nothing if file missing)
if _env_path:
    load_dotenv(dotenv_path=_env_path, override=False)

# If provided on CLI, set DB_PASS to override .env/env
_cli_db_pass = _get_cli_db_pass(sys.argv)
if _cli_db_pass:
    # Ensure it is available for downstream imports (e.g., connection pool)
    os.environ["DB_PASS"] = _cli_db_pass

from source_code.crud.auth_api_routes import router as auth_router
from source_code.crud.holding_api_routes import router as holding_router
from source_code.crud.portfolio_api_routes import router as portfolio_router
from source_code.crud.security_api_routes import router as security_router
from source_code.crud.security_price_api_routes import router as security_price_router
from source_code.crud.external_platform_api_routes import router as platform_router
from source_code.crud.transaction_api_routes import router as transaction_router
from source_code.crud.user_api_routes import router as user_router, router_api as user_api_router

from contextlib import asynccontextmanager

@asynccontextmanager
async def _lifespan(app: FastAPI):
    # Startup
    resolved = str(_env_path) if '_env_path' in globals() and _env_path else 'none'
    print(f"[startup] RUNNING_ENV={os.getenv('RUNNING_ENV', '')} (selected env: {_SELECTED_ENV}, file: {resolved})")
    try:
        yield
    finally:
        # Shutdown (place for cleanup if needed in future)
        pass

app = FastAPI(title="Portfolio Manager", lifespan=_lifespan)

# Enable gzip compression for responses (static and API)
app.add_middleware(GZipMiddleware, minimum_size=500)

# Allow CORS from vite (front-end) to send requests to the server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Must be False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Removed hardcoded root route to allow React app serving
# @app.get("/")
# async def root():
#     print('in main')
#     return {"message": "Hello World!"}


# in your FastAPI app setup file
app.include_router(auth_router)

# app.include_router(portfolio.router, prefix="/portfolios")
# app.include_router(holding.router, prefix="/holdings")
#
app.include_router(user_router)
app.include_router(user_api_router)
app.include_router(security_router)
app.include_router(portfolio_router)
app.include_router(platform_router)
app.include_router(transaction_router)
app.include_router(holding_router)
app.include_router(security_price_router)

# Mount static files for React frontend
if os.path.exists("dist"):
    # Serve built assets under /assets (JS/CSS)
    app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")

    # Serve the SPA index.html at root and for any non-API route
    from fastapi.responses import HTMLResponse

    @app.get("/", response_class=HTMLResponse)
    async def serve_index_root():
        return FileResponse("dist/index.html")

    # Fallback for client-side routes (React Router) excluding API and docs/openapi
    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def serve_index_spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            # Let FastAPI handle these (should be matched by routers)
            from fastapi import HTTPException
            raise HTTPException(status_code=404)
        # Serve real file from dist root if it exists (e.g., favicon.svg, manifest)
        candidate = os.path.join("dist", full_path)
        if os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse("dist/index.html")
else:
    # If dist doesn't exist, provide helpful message
    @app.get("/")
    async def root_fallback():
        return {"message": "React build not found. Build the frontend first with 'npm run build'"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
