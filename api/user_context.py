"""
Request-scoped context for the currently authenticated user.

Tools can read this to behave per-user without changing tool signatures.
"""

from __future__ import annotations

import contextvars
from typing import Optional


_current_user_id: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar(
    "current_user_id", default=None
)


def set_current_user_id(user_id: Optional[int]) -> contextvars.Token:
    return _current_user_id.set(user_id)


def reset_current_user_id(token: contextvars.Token) -> None:
    _current_user_id.reset(token)


def get_current_user_id() -> Optional[int]:
    return _current_user_id.get()


