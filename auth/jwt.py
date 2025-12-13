from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        # Fail early in production; local dev can set it in .env
        raise RuntimeError("JWT_SECRET is not set")
    return secret


def create_access_token(user_id: int, username: str, expires_minutes: int = 60 * 24 * 7) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "username": username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


