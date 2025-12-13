from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import get_db
from auth.jwt import create_access_token
from auth.passwords import hash_password, verify_password
from db.models import User


router = APIRouter()


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing is not None:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(username=payload.username, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user_id=user.id, username=user.username)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user_id=user.id, username=user.username)
    return TokenResponse(access_token=token)


