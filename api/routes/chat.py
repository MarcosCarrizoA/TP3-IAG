from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from api.deps import get_current_user
from api.user_context import set_current_user_id, reset_current_user_id
from api import state
from db.models import User
from tools.memory import get_similar_contexts, save_context
from tools.playlists import list_playlists


router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str


HELP_TEXT = (
    "Comandos disponibles:\n"
    "- help: muestra esta ayuda\n"
    "- playlists: lista tus playlists\n"
    "- memory: muestra memoria/contextos previos (solo para el modelo)\n"
    "\n"
    "También podés pedir recomendaciones y gestionar playlists por chat, por ejemplo:\n"
    "- 'Recomendame música para estudiar con lluvia'\n"
    "- 'Agregá una playlist llamada Focus Pro con descripción lo-fi para estudiar'\n"
    "- 'Editá la playlist Focus Flow y poné: lo-fi + ambient para concentración'\n"
    "- 'Borrá la playlist Rainy Mood'\n"
)


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
):
    if state.agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Set request-scoped user id so tools (playlists/memory) can behave per-user.
    token = set_current_user_id(user.id)
    try:
        cmd = payload.message.strip()
        cmd_l = cmd.lower()

        # Cheap commands (no model call).
        if cmd_l == "help":
            return ChatResponse(reply=HELP_TEXT)
        if cmd_l == "playlists":
            return ChatResponse(reply=list_playlists())
        if cmd_l in ("memory", "memoria"):
            return ChatResponse(reply=get_similar_contexts("", top_k=10))

        # Retrieve compact per-user memory (Chroma) and inject it into the prompt.
        memory = get_similar_contexts(payload.message, top_k=3)

        config = {"configurable": {"thread_id": f"user:{user.id}"}}
        messages = [
            SystemMessage(content=state.agent._system_prompt),
            SystemMessage(content=f"Memoria relevante del usuario (si existe):\n{memory}"),
            HumanMessage(content=payload.message),
        ]
        try:
            response = state.agent.invoke({"messages": messages}, config)
        except Exception as e:
            # Gemini quota/rate-limit errors should surface as a clean 429 to the client UI.
            msg = str(e)
            if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
                raise HTTPException(
                    status_code=429,
                    detail=(
                        "Gemini API quota exceeded (429 RESOURCE_EXHAUSTED). "
                        "Check your Google AI Studio quotas/billing or try again later."
                    ),
                )
            raise

        last = response["messages"][-1]
        reply = getattr(last, "content", str(last))

        # Persist a compact memory summary for future retrieval (Chroma).
        # Keep it short to minimize embedding/storage cost.
        summary = f"Usuario: {payload.message.strip()}\nAsistente: {str(reply).strip()}"
        if len(summary) > 900:
            summary = summary[:900]
        save_context(summary)

        return ChatResponse(reply=reply)
    finally:
        reset_current_user_id(token)


