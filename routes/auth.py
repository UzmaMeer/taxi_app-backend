"""
Authentication routes — register and login with MongoDB.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from database import get_database
import hashlib
import secrets

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/register")
async def register(req: RegisterRequest):
    db = get_database()

    existing = await db.users.find_one({"email": req.email.lower().strip()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_doc = {
        "full_name": req.full_name.strip(),
        "email": req.email.lower().strip(),
        "password_hash": _hash(req.password),
        "role": "driver",  # Default role for standard signup
        "token": secrets.token_hex(32),
    }
    result = await db.users.insert_one(user_doc)

    return {
        "message": "Registration successful",
        "user": {
            "id": str(result.inserted_id),
            "full_name": user_doc["full_name"],
            "email": user_doc["email"],
            "role": user_doc["role"],
            "token": user_doc["token"],
        },
    }


@router.post("/login")
async def login(req: LoginRequest):
    db = get_database()

    user = await db.users.find_one({
        "email": req.email.lower().strip(),
        "password_hash": _hash(req.password),
    })

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Rotate token on each login
    new_token = secrets.token_hex(32)
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"token": new_token}})

    return {
        "message": "Login successful",
        "user": {
            "id": str(user["_id"]),
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user.get("role", "driver"),
            "token": new_token,
        },
    }


@router.get("/me")
async def get_me(token: str):
    db = get_database()
    user = await db.users.find_one({"token": token})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {
        "id": str(user["_id"]),
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user.get("role", "driver"),
    }


class UpdateProfileRequest(BaseModel):
    full_name: str = None
    password: str = None


@router.put("/profile/update")
async def update_profile(req: UpdateProfileRequest, token: str):
    db = get_database()
    user = await db.users.find_one({"token": token})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    update_data = {}
    if req.full_name is not None and req.full_name.strip():
        update_data["full_name"] = req.full_name.strip()
    if req.password is not None and req.password.strip():
        update_data["password_hash"] = _hash(req.password)
        
    if update_data:
        await db.users.update_one({"_id": user["_id"]}, {"$set": update_data})
        
    return {"message": "Profile updated successfully"}

