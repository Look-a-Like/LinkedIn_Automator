from fastapi import APIRouter, HTTPException, Response, Request, Header
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from ..models.user import UserCreate, UserResponse, UserLogin
from ..db import db

# Setup password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user(email: str):
    user = await db.users.find_one({"email": email})
    if user:
        return user
    return None

async def authenticate_user(email: str, password: str):
    user = await get_user(email)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

# Helper function to add CORS headers with dynamic origin support
def add_cors_headers(response: Response, request_origin: str = None):
    # List of allowed origins
    allowed_origins = [
        "http://localhost:5173",  # React frontend URL
        "http://localhost:8501",  # Streamlit URL
        "http://127.0.0.1:5173",  # Alternative React URL
        "http://127.0.0.1:8501",  # Alternative Streamlit URL
    ]

    # Fix for React frontend - always use React URL for now
    # This ensures the Access-Control-Allow-Origin header matches the requesting origin
    response.headers["Access-Control-Allow-Origin"] = request_origin or "http://localhost:5173"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"

# Routes
@router.post("/register", response_model=UserResponse)
async def create_user(user: UserCreate, response: Response, request: Request = None):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create hashed password
    hashed_password = get_password_hash(user.password)

    # Create user in database with user_id field
    user_data = user.dict()
    user_data.pop("password")  # Remove plain password
    user_data["hashed_password"] = hashed_password
    user_data["user_id"] = f"user_{datetime.utcnow().timestamp()}"  # Simple user_id
    user_data["created_at"] = datetime.utcnow().isoformat()

    result = await db.users.insert_one(user_data)

    # Get created user from database
    created_user = await db.users.find_one({"_id": result.inserted_id})

    # ✅ Add full CORS headers
    add_cors_headers(response, request.headers.get("origin"))

    return created_user

@router.post("/login")
async def login(user_data: UserLogin, response: Response, request: Request = None):
    user = await authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )

    add_cors_headers(response, request.headers.get("origin"))

    return {
        "access_token": user["user_id"],  # Just using user_id as a simple token
        "token_type": "bearer",
        "user": {
            "email": user["email"],
            "username": user["username"],
            "id": str(user["_id"]),
            "user_id": user["user_id"]
        }
    }

@router.options("/{path:path}")
async def options_handler(path: str, response: Response, request: Request = None):
    """
    Handle OPTIONS requests for all endpoints under /users
    This is crucial for CORS preflight requests
    """
    add_cors_headers(response, request.headers.get("origin"))
    return {}


async def get_current_user(user_id: str = Header(..., alias="X-User-ID")):
    """
    Extracts the user_id from request headers.
    Simulates authentication logic by returning a basic user dict.
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID header missing")

    return {"_id": user_id}