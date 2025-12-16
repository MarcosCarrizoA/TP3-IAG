"""
Request-scoped callback context.

We use contextvars so tools/subagents executed in threadpools still inherit the
same callback handler (AnyIO copies context into worker threads).
"""

from __future__ import annotations

import contextvars
from typing import Any, Optional


_callbacks: contextvars.ContextVar[Optional[list[Any]]] = contextvars.ContextVar(
    "lc_callbacks", default=None
)
_agent_label: contextvars.ContextVar[str] = contextvars.ContextVar("agent_label", default="main_agent")


def set_callbacks(callbacks: Optional[list[Any]]) -> contextvars.Token:
    return _callbacks.set(callbacks)


def reset_callbacks(token: contextvars.Token) -> None:
    _callbacks.reset(token)


def get_callbacks() -> Optional[list[Any]]:
    return _callbacks.get()


def set_agent_label(label: str) -> contextvars.Token:
    return _agent_label.set(label)


def reset_agent_label(token: contextvars.Token) -> None:
    _agent_label.reset(token)


def get_agent_label() -> str:
    return _agent_label.get()


