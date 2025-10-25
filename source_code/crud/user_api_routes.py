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

router = APIRouter(prefix="/users", tags=["Users"]) 
# Also expose the same endpoints under /api/users for the front-end
router_api = APIRouter(prefix="/api/users", tags=["Users"])

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
@router_api.post("/", response_model=UserDtl)
def save_user(user: UserDtlInput):
    # Enforce unique email (if provided)
    if getattr(user, 'email', None):
        existing = user_crud.get_by_email(user.email)
        if existing:
            raise HTTPException(status_code=400, detail=f"A user with email '{user.email}' already exists")
    # Hash the password if provided; store hash via CRUD (mapping password->password_hash)
    if user.password:
        user.password = auth_utils.hash_password(user.password)
    return user_crud.save(user)


@router.get("", response_model=list[UserDtl])
@router.get("/", response_model=list[UserDtl])
@router_api.get("", response_model=list[UserDtl])
@router_api.get("/", response_model=list[UserDtl])
def list_users():
    return user_crud.list_all()


# Bulk save JSON array
@router.post("/bulk", response_model=list[UserDtl])
@router_api.post("/bulk", response_model=list[UserDtl])
def save_users_bulk(users: list[UserDtlInput]):
    if not users:
        return []
    # Normalize and check duplicate emails within payload
    seen = {}
    dups = set()
    for idx, u in enumerate(users):
        em = (getattr(u, 'email', None) or '').strip().lower()
        if not em:
            continue
        if em in seen:
            dups.add(em)
        else:
            seen[em] = idx
    if dups:
        dup_list = ", ".join(sorted(dups))
        raise HTTPException(status_code=400, detail=f"Duplicate emails in payload: {dup_list}")
    # Check against existing DB
    conflicts = []
    for em in seen.keys():
        if user_crud.get_by_email(em):
            conflicts.append(em)
    if conflicts:
        conf_list = ", ".join(sorted(conflicts))
        raise HTTPException(status_code=400, detail=f"Users already exist for emails: {conf_list}")
    # Hash passwords and forward
    items: list[UserDtlInput] = []
    for u in users:
        if u.password:
            u.password = auth_utils.hash_password(u.password)
        items.append(u)
    return user_crud.save_many(items)


# CSV upload for users (headers: first_name, last_name, [email], [password])
@router.post("/bulk-csv", response_model=list[UserDtl])
@router_api.post("/bulk-csv", response_model=list[UserDtl])
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
    email_rows: dict[str, int] = {}
    dups_in_file = set()
    for row in reader:
        row_num += 1

        def get_val(k: str) -> str:
            return (row.get(k) or row.get(k.upper()) or row.get(k.title()) or "").strip()

        first_name = get_val("first_name")
        last_name = get_val("last_name")
        email_raw = get_val("email")
        email = email_raw or None
        password = get_val("password") or None
        if not first_name or not last_name:
            raise HTTPException(status_code=400, detail=f"Row {row_num}: 'first_name' and 'last_name' are required")
        # Track duplicates in file
        if email:
            em_norm = email.strip().lower()
            if em_norm in email_rows:
                dups_in_file.add(em_norm)
            else:
                email_rows[em_norm] = row_num
        if password:
            password = auth_utils.hash_password(password)
        items.append(UserDtlInput(first_name=first_name, last_name=last_name, email=email, password=password))
    if dups_in_file:
        dup_list = ", ".join(sorted(dups_in_file))
        raise HTTPException(status_code=400, detail=f"Duplicate emails in file: {dup_list}")
    if not items:
        return []
    # Check against existing DB
    conflicts = []
    for em in email_rows.keys():
        if user_crud.get_by_email(em):
            conflicts.append(em)
    if conflicts:
        conf_list = ", ".join(sorted(conflicts))
        raise HTTPException(status_code=400, detail=f"Users already exist for emails: {conf_list}")
    return user_crud.save_many(items)


# CSV export endpoint
@router.get("/export.csv")
@router_api.get("/export.csv")
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
@router_api.get("/{user_id}", response_model=UserDtl)
def get_user(user_id: int):
    user = user_crud.get_security(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserDtl)
@router_api.put("/{user_id}", response_model=UserDtl)
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
@router_api.delete("/{user_id}", response_model=dict)
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
@router_api.post("/login")
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
        "user": {
            "id": user.user_id,
            "email": user.email,
            "is_admin": getattr(user, "is_admin", False),
            "first_name": getattr(user, "first_name", None),
            "last_name": getattr(user, "last_name", None),
            "full_name": f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip(),
        },
    }
