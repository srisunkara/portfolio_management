# source_code/crud/user_api_routes.py
import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from source_code.crud.user_crud_operations import user_crud
from source_code.models.models import UserDtl, UserDtlInput
from source_code.utils import auth_utils

router = APIRouter(prefix="/api/users", tags=["Users"])

# Replace with your real CRUD and model imports
# from source_code.crud.user_crud_operations import user_crud
# from source_code.models.models import User


# Token settings
SECRET = os.environ.get("APP_TOKEN_SECRET", "change-this-secret").encode()
TOKEN_TTL_MIN = int(os.environ.get("APP_TOKEN_TTL_MIN", "120"))

# Stored password format:
# pbkdf2_sha256$<iterations>$<salt_b64>$<hash_b64>
ALGO = "pbkdf2_sha256"
DEFAULT_ITERATIONS = 100_000
HASH_LEN = 32  # 256-bit
SALT_LEN = 16


@router.post("/", response_model=UserDtl)
def save_user(user: UserDtlInput):
    # Hash the password if provided; store hash via CRUD (mapping password->password_hash)
    if user.password:
        user.password = auth_utils.hash_password(user.password)
    return user_crud.save(user)


@router.get("/", response_model=list[UserDtl])
def list_users():
    return user_crud.list_all()


# Bulk save JSON array
@router.post("/bulk", response_model=list[UserDtl])
def save_users_bulk(users: list[UserDtlInput]):
    if not users:
        return []
    items: list[UserDtlInput] = []
    for u in users:
        if u.password:
            u.password = auth_utils.hash_password(u.password)
        items.append(u)
    return user_crud.save_many(items)


# CSV upload for users (headers: first_name, last_name, [email], [password])
@router.post("/bulk-csv", response_model=list[UserDtl])
async def upload_users_csv(file):
    from fastapi import UploadFile, File
    import csv, io
    if not isinstance(file, UploadFile) or not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    headers = [h.strip().lower() for h in (reader.fieldnames or [])]
    required = {"first_name", "last_name"}
    missing = required - set(headers)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required CSV headers: {', '.join(sorted(missing))}")
    items: list[UserDtlInput] = []
    row_num = 1
    for row in reader:
        row_num += 1

        def get_val(k: str) -> str:
            return (row.get(k) or row.get(k.upper()) or row.get(k.title()) or "").strip()

        first_name = get_val("first_name")
        last_name = get_val("last_name")
        email = get_val("email") or None
        password = get_val("password") or None
        if not first_name or not last_name:
            raise HTTPException(status_code=400, detail=f"Row {row_num}: 'first_name' and 'last_name' are required")
        if password:
            password = auth_utils.hash_password(password)
        items.append(UserDtlInput(first_name=first_name, last_name=last_name, email=email, password=password))
    if not items:
        return []
    return user_crud.save_many(items)


# CSV export endpoint
@router.get("/export.csv")
def export_users_csv():
    import csv, io
    from fastapi.responses import Response
    items = user_crud.list_all()
    output = io.StringIO()
    writer = csv.writer(output)
    header = ["user_id", "first_name", "last_name", "email", "created_ts", "last_updated_ts"]
    writer.writerow(header)
    for u in items:
        writer.writerow([
            getattr(u, "user_id", ""),
            getattr(u, "first_name", ""),
            getattr(u, "last_name", ""),
            getattr(u, "email", ""),
            getattr(u, "created_ts", ""),
            getattr(u, "last_updated_ts", ""),
        ])
    csv_data = output.getvalue()
    output.close()
    return Response(content=csv_data, media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="users.csv"'})


@router.get("/{user_id}", response_model=UserDtl)
def get_user(user_id: int):
    user = user_crud.get_security(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserDtl)
def update_user(user_id: int, user: UserDtlInput):
    try:
        # If a plain password is provided from the form, hash it before persisting
        if getattr(user, 'password', None):
            user.password = auth_utils.hash_password(user.password)
        return user_crud.update(user_id, user)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except KeyError:
        raise HTTPException(status_code=404, detail="User not found")


@router.delete("/{user_id}", response_model=dict)
def delete_user(user_id: int):
    deleted = user_crud.delete(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"deleted": True}




def sign_token(payload: dict) -> str:
    data = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    sig = hmac.new(SECRET, data, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(data + b"." + sig).decode()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
def login(body: LoginRequest):
    print(f"DEBUG: Login attempt for email: {body.email}")
    
    if not body.email or not body.password:
        print("DEBUG: Empty email or password")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = user_crud.get_by_email(body.email)
    print(f"DEBUG: User found: {user is not None}")
    if user:
        print(f"DEBUG: User has password_hash: {user.password_hash is not None}")
        print(f"DEBUG: Password hash: {user.password_hash}")
    
    if user is None or not user.password_hash:
        print("DEBUG: No user found or no password hash")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    password_valid = auth_utils.verify_password(body.password, user.password_hash)
    print(f"DEBUG: Password verification result: {password_valid}")
    
    if not password_valid:
        print("DEBUG: Password verification failed")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    print("DEBUG: Login successful, generating token")
    now = datetime.utcnow()
    payload = {"sub": str(user.user_id), "email": user.email, "exp": (now + timedelta(minutes=TOKEN_TTL_MIN)).timestamp()}
    token = sign_token(payload)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.user_id, "email": user.email, "is_admin": getattr(user, "is_admin", False)},
    }
