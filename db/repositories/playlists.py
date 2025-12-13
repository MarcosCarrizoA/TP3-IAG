from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.models import Playlist


def list_playlists_for_user(db: Session, user_id: int) -> list[Playlist]:
    stmt = select(Playlist).where(Playlist.user_id == user_id).order_by(Playlist.name.asc())
    return list(db.execute(stmt).scalars().all())


def create_playlist_for_user(db: Session, user_id: int, name: str, description: str) -> Playlist:
    p = Playlist(user_id=user_id, name=name, description=description)
    db.add(p)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # if duplicate name, overwrite (simple UX)
        existing = db.execute(
            select(Playlist).where(Playlist.user_id == user_id, Playlist.name == name)
        ).scalar_one_or_none()
        if existing is None:
            raise
        existing.description = description
        existing.updated_at = datetime.utcnow()
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing
    db.refresh(p)
    return p


def update_playlist_for_user(
    db: Session, user_id: int, playlist_id: int, description: str
) -> Playlist | None:
    p = db.get(Playlist, playlist_id)
    if p is None or p.user_id != user_id:
        return None
    p.description = description
    p.updated_at = datetime.utcnow()
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def delete_playlist_for_user(db: Session, user_id: int, playlist_id: int) -> bool:
    p = db.get(Playlist, playlist_id)
    if p is None or p.user_id != user_id:
        return False
    db.delete(p)
    db.commit()
    return True


