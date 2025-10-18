from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import hmac, hashlib, base64, json

# Replace these with your real services and models
# e.g. from source_code.crud.user_crud_operations import user_crud
# from source_code.models.models import User

router = APIRouter(prefix="/api/auth", tags=["Auth"])

SECRET = b"change-this-secret"
TOKEN_TTL_MIN = 120

class LoginRequest(BaseModel):
    username: str
    password: str

def sign_token(payload: dict) -> str:
    data = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    sig = hmac.new(SECRET, data, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(data + b"." + sig).decode()

def verify_password(plain: str, stored_hash: str) -> bool:
    # Replace with your actual verification (e.g., PBKDF2/bcrypt)
    return hmac.compare_digest(
        hashlib.sha256(plain.encode()).hexdigest(),
        stored_hash,
    )

@router.post("/login")
def login(body: LoginRequest):
    # user = user_crud.get_by_username(body.username)
    # if not user or not verify_password(body.password, user.password_hash):
    #     raise HTTPException(status_code=401, detail="Invalid credentials")

    # Demo only: accept any non-empty credentials
    if not body.username or not body.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    now = datetime.utcnow()
    payload = {"sub": body.username, "exp": (now + timedelta(minutes=TOKEN_TTL_MIN)).timestamp()}
    token = sign_token(payload)

    user = {"id": 1, "username": body.username}  # Replace with real user fields
    return {"access_token": token, "token_type": "bearer", "user": user}