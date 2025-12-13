from __future__ import annotations

from typing import Generator

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from auth.jwt import decode_access_token
from db.models import User
from db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    payload = decode_access_token(creds.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.get(User, int(user_id))
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


