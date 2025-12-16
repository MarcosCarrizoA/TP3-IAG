"""
Request-scoped usage accounting (token counts).

This lets sub-components (like the context sub-agent) contribute usage to a single
`/chat` response without changing tool signatures.
"""

from __future__ import annotations

import contextvars
from typing import Any, Optional


UsageEntry = dict[str, Any]

_entries: contextvars.ContextVar[list[UsageEntry]] = contextvars.ContextVar("usage_entries", default=[])


def start_request() -> contextvars.Token:
    """Reset entries for this request context."""
    return _entries.set([])


def end_request(token: contextvars.Token) -> None:
    _entries.reset(token)


def add_usage(agent: str, usage: Optional[dict[str, Any]]) -> None:
    if not usage:
        return
    e = dict(usage)
    e["agent"] = agent
    cur = list(_entries.get())
    cur.append(e)
    _entries.set(cur)


def get_breakdown() -> list[UsageEntry]:
    return list(_entries.get())


def sum_usage(entries: list[UsageEntry]) -> dict[str, int]:
    total_in = 0
    total_out = 0
    total_all = 0
    for e in entries:
        if isinstance(e.get("input_tokens"), int):
            total_in += int(e["input_tokens"])
        if isinstance(e.get("output_tokens"), int):
            total_out += int(e["output_tokens"])
        if isinstance(e.get("total_tokens"), int):
            total_all += int(e["total_tokens"])
    out: dict[str, int] = {}
    if total_in:
        out["input_tokens"] = total_in
    if total_out:
        out["output_tokens"] = total_out
    if total_all:
        out["total_tokens"] = total_all
    return out


