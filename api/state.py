from __future__ import annotations

from typing import Optional, Any


# Global app state (single-process). Railway should run 1 instance for SQLite+Volume.
agent: Optional[Any] = None


