import re
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator

from app.db.database import get_db, IntegrityError
from app.core.security import hash_password, verify_password, create_access_token
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])

_PASSWORD_MIN_LENGTH = 8


class SignupRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < _PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {_PASSWORD_MIN_LENGTH} characters long.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(request: SignupRequest):
    user_id = str(uuid4())
    password_hash = hash_password(request.password)

    with get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
                (user_id, request.email.lower(), password_hash),
            )
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

    token = create_access_token(user_id=user_id, email=request.email.lower())
    return TokenResponse(
        access_token=token,
        user={"id": user_id, "email": request.email.lower()},
    )


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, email, password_hash FROM users WHERE email = ?",
            (request.email.lower(),),
        ).fetchone()

    # Deliberately the same error for "no such user" and "wrong password" —
    # confirming which one it was lets an attacker enumerate valid emails.
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
    )

    if row is None:
        raise invalid_credentials
    if not verify_password(request.password, row["password_hash"]):
        raise invalid_credentials

    token = create_access_token(user_id=row["id"], email=row["email"])
    return TokenResponse(
        access_token=token,
        user={"id": row["id"], "email": row["email"]},
    )


@router.get("/me")
def get_me(user_id: str = Depends(get_current_user)):
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return {"id": row["id"], "email": row["email"]}