from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from db.models import User
from db.repositories.messages import list_messages_for_user


router = APIRouter()


@router.get("/history")
def history(
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    msgs = list_messages_for_user(db, user_id=user.id, limit=limit, offset=offset)
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in msgs
    ]


