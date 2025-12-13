from __future__ import annotations

from fastapi import FastAPI

from agents import create_music_agent
from db.session import init_db
from vectorstores import initialize_knowledge_vectorstore, initialize_memory_vectorstore

from api.routes.auth import router as auth_router
from api.routes.chat import router as chat_router
from api.routes.playlists import router as playlists_router
from api.routes.history import router as history_router
from api.routes.health import router as health_router
from api import state


app = FastAPI(title="Music Recommendation Agent")

app.include_router(health_router)
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(chat_router, tags=["chat"])
app.include_router(playlists_router, tags=["playlists"])
app.include_router(history_router, tags=["history"])


@app.on_event("startup")
def _startup() -> None:
    # DB tables
    init_db()

    # Vectorstores (ensure directories exist / load if present)
    initialize_memory_vectorstore()
    initialize_knowledge_vectorstore()

    # Agent (heavy init once)
    state.agent = create_music_agent()


