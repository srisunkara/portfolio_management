# main.py
import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from source_code.crud.auth_api_routes import router as auth_router
from source_code.crud.holding_api_routes import router as holding_router
from source_code.crud.portfolio_api_routes import router as portfolio_router
from source_code.crud.security_api_routes import router as security_router
from source_code.crud.security_price_api_routes import router as security_price_router
from source_code.crud.external_platform_api_routes import router as platform_router
from source_code.crud.transaction_api_routes import router as transaction_router
from source_code.crud.user_api_routes import router as user_router

app = FastAPI(title="Portfolio Manager")

# Allow CORS from vite (front-end) to send requests to the server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Must be False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    print('in main')
    return {"message": "Hello World!"}


# in your FastAPI app setup file
app.include_router(auth_router)

# app.include_router(portfolio.router, prefix="/portfolios")
# app.include_router(holding.router, prefix="/holdings")
#
app.include_router(user_router)
app.include_router(security_router)
app.include_router(portfolio_router)
app.include_router(platform_router)
app.include_router(transaction_router)
app.include_router(holding_router)
app.include_router(security_price_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
