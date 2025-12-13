from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv

from agents import create_music_agent
from db.session import init_db
from vectorstores import initialize_knowledge_vectorstore, initialize_memory_vectorstore

from api.routes.auth import router as auth_router
from api.routes.chat import router as chat_router
from api.routes.playlists import router as playlists_router
from api.routes.health import router as health_router
from api import state


load_dotenv()

app = FastAPI(title="Music Recommendation Agent")

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
cors_origins = [o.strip() for o in cors_origins if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(chat_router, tags=["chat"])
app.include_router(playlists_router, tags=["playlists"])


@app.on_event("startup")
def _startup() -> None:
    # DB tables
    init_db()

    # Vectorstores (ensure directories exist / load if present)
    initialize_memory_vectorstore()
    initialize_knowledge_vectorstore()

    # Agent (heavy init once)
    state.agent = create_music_agent()


