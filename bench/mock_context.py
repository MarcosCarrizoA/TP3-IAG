"""
Benchmark-only request-scoped mocks for external context providers (weather/time/location).

This avoids hitting real external APIs and makes benchmarks deterministic per-case.
"""

from __future__ import annotations

import contextvars
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class APIMocks:
    location: Optional[str] = None
    time: Optional[str] = None  # "HH:MM"
    season: Optional[str] = None
    weather: Optional[str] = None
    temperature_c: Optional[float] = None


_mocks: contextvars.ContextVar[Optional[APIMocks]] = contextvars.ContextVar("bench_api_mocks", default=None)


def set_api_mocks(mocks: Optional[APIMocks]) -> contextvars.Token:
    return _mocks.set(mocks)


def reset_api_mocks(token: contextvars.Token) -> None:
    _mocks.reset(token)


def get_api_mocks() -> Optional[APIMocks]:
    return _mocks.get()


