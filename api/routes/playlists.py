from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from db.models import User
from db.repositories.playlists import (
    list_playlists_for_user,
    create_playlist_for_user,
    update_playlist_for_user,
    delete_playlist_for_user,
)


router = APIRouter()


class PlaylistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = Field(min_length=1, max_length=1000)


class PlaylistUpdate(BaseModel):
    description: str = Field(min_length=1, max_length=1000)


@router.get("/playlists")
def list_playlists(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    playlists = list_playlists_for_user(db, user_id=user.id)
    return [{"id": p.id, "name": p.name, "description": p.description} for p in playlists]


@router.post("/playlists")
def create_playlist(
    payload: PlaylistCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = create_playlist_for_user(db, user_id=user.id, name=payload.name, description=payload.description)
    return {"id": p.id, "name": p.name, "description": p.description}


@router.put("/playlists/{playlist_id}")
def update_playlist(
    playlist_id: int,
    payload: PlaylistUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = update_playlist_for_user(db, user_id=user.id, playlist_id=playlist_id, description=payload.description)
    if p is None:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return {"id": p.id, "name": p.name, "description": p.description}


@router.delete("/playlists/{playlist_id}")
def delete_playlist(
    playlist_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ok = delete_playlist_for_user(db, user_id=user.id, playlist_id=playlist_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return {"deleted": True}


