from __future__ import annotations

from passlib.context import CryptContext


# Use PBKDF2-SHA256 to avoid bcrypt's 72-byte password limit and
# platform-specific backend issues (common on Windows).
_pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


