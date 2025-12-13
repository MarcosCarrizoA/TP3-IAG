from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Message


def add_message(db: Session, user_id: int, role: str, content: str) -> Message:
    msg = Message(user_id=user_id, role=role, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def list_messages_for_user(db: Session, user_id: int, limit: int = 50, offset: int = 0) -> list[Message]:
    stmt = (
        select(Message)
        .where(Message.user_id == user_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars().all())


