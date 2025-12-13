from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from langchain_core.messages import SystemMessage, HumanMessage

from api.deps import get_current_user, get_db
from api.user_context import set_current_user_id, reset_current_user_id
from api import state
from db.models import User
from db.repositories.messages import add_message


router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if state.agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Set request-scoped user id so tools (playlists/memory) can behave per-user.
    token = set_current_user_id(user.id)
    try:
        add_message(db, user_id=user.id, role="user", content=payload.message)

        config = {"configurable": {"thread_id": f"user:{user.id}"}}
        messages = [
            SystemMessage(content=state.agent._system_prompt),
            HumanMessage(content=payload.message),
        ]
        response = state.agent.invoke({"messages": messages}, config)

        last = response["messages"][-1]
        reply = getattr(last, "content", str(last))

        add_message(db, user_id=user.id, role="assistant", content=reply)

        return ChatResponse(reply=reply)
    finally:
        reset_current_user_id(token)


