from __future__ import annotations

from fastapi import APIRouter


router = APIRouter()


@router.get("/health", tags=["ops"])
def health():
    return {"ok": True}


