from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Any, Optional

from api.deps import get_current_user
from api.user_context import set_current_user_id, reset_current_user_id
from api import state
from db.models import User
from tools.memory import get_similar_contexts, save_context
from tools.playlists import list_playlists
from api.callback_context import set_callbacks, reset_callbacks, set_agent_label, reset_agent_label
from api.llm_usage_callback import LLMUsageCallbackHandler


router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str
    expense: Optional[dict[str, Any]] = None


def _group_usage_breakdown(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Group token usage entries by agent to avoid duplicated rows in the UI.
    This happens when an agent performs multiple internal LLM calls (e.g. plan + answer).
    """
    grouped: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    models_seen: dict[str, set[str]] = {}

    for e in entries:
        agent = str(e.get("agent") or "agent")
        if agent not in grouped:
            grouped[agent] = {"agent": agent, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            order.append(agent)
            models_seen[agent] = set()

        if isinstance(e.get("input_tokens"), int):
            grouped[agent]["input_tokens"] += int(e["input_tokens"])
        if isinstance(e.get("output_tokens"), int):
            grouped[agent]["output_tokens"] += int(e["output_tokens"])
        if isinstance(e.get("total_tokens"), int):
            grouped[agent]["total_tokens"] += int(e["total_tokens"])

        m = e.get("model")
        if isinstance(m, str) and m.strip():
            models_seen[agent].add(m.strip())

    out: list[dict[str, Any]] = []
    for agent in order:
        row = grouped[agent]
        # If the agent used exactly one model across internal calls, keep it.
        ms = models_seen.get(agent) or set()
        if len(ms) == 1:
            row["model"] = next(iter(ms))
        out.append(row)
    return out


def _extract_usage(msg: Any) -> Optional[dict[str, Any]]:
    """
    Best-effort extraction of token usage from LangChain message metadata.
    Different providers store this in different fields.
    """
    candidates: list[Any] = []
    for attr in ("usage_metadata", "response_metadata", "additional_kwargs"):
        try:
            v = getattr(msg, attr, None)
            if v:
                candidates.append(v)
        except Exception:
            pass

    # Some providers nest usage under response_metadata["usage_metadata"] or token_usage keys.
    for c in candidates:
        if isinstance(c, dict):
            for key in ("usage_metadata", "token_usage", "usage", "usageMetadata"):
                inner = c.get(key)
                if isinstance(inner, dict) and inner:
                    candidates.append(inner)

    for c in candidates:
        if not isinstance(c, dict):
            continue

        # Normalize common shapes
        input_tokens = c.get("input_tokens") or c.get("prompt_tokens") or c.get("inputTokenCount")
        output_tokens = c.get("output_tokens") or c.get("completion_tokens") or c.get("outputTokenCount")
        total_tokens = c.get("total_tokens") or c.get("totalTokenCount")

        # Gemini often provides total, and sometimes separate counts.
        if input_tokens is None and "promptTokenCount" in c:
            input_tokens = c.get("promptTokenCount")
        if output_tokens is None and "candidatesTokenCount" in c:
            output_tokens = c.get("candidatesTokenCount")
        if total_tokens is None and "totalTokenCount" in c:
            total_tokens = c.get("totalTokenCount")

        if any(x is not None for x in (input_tokens, output_tokens, total_tokens)):
            out: dict[str, Any] = {}
            if input_tokens is not None:
                out["input_tokens"] = int(input_tokens)
            if output_tokens is not None:
                out["output_tokens"] = int(output_tokens)
            if total_tokens is not None:
                out["total_tokens"] = int(total_tokens)

            # Optional: model name if available
            model = c.get("model") or c.get("model_name")
            if model:
                out["model"] = str(model)
            return out
    return None


def _content_to_text(content: Any) -> str:
    """Normalize LangChain message content to a plain string."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    # Some providers return a list of parts: [{"type":"text","text":"..."}]
    if isinstance(content, list) or isinstance(content, tuple):
        parts: list[str] = []
        for p in content:
            if isinstance(p, str):
                parts.append(p)
                continue
            if isinstance(p, dict):
                # Gemini style
                if isinstance(p.get("text"), str):
                    parts.append(p["text"])
                    continue
                # Generic fallback: stringify dict
                parts.append(str(p))
                continue
            parts.append(str(p))
        return "\n".join([x for x in parts if x])
    if isinstance(content, dict):
        if isinstance(content.get("text"), str):
            return content["text"]
        return str(content)
    return str(content)


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
    cb = LLMUsageCallbackHandler()
    cb_token = set_callbacks([cb])
    label_token = set_agent_label("main_agent")
    try:
        cmd = payload.message.strip()
        cmd_l = cmd.lower()

        # Cheap commands (no model call).
        if cmd_l == "help":
            return ChatResponse(reply=HELP_TEXT, expense=None)
        if cmd_l == "playlists":
            return ChatResponse(reply=list_playlists(), expense=None)
        if cmd_l in ("memory", "memoria"):
            return ChatResponse(reply=get_similar_contexts("", top_k=10), expense=None)

        # Retrieve compact per-user memory (Chroma) and inject it into the prompt.
        memory = get_similar_contexts(payload.message, top_k=3)

        messages = [
            SystemMessage(content=state.agent._system_prompt),
            SystemMessage(content=f"Memoria relevante del usuario (si existe):\n{memory}"),
            HumanMessage(content=payload.message),
        ]
        try:
            response = state.agent.invoke(
                {"messages": messages},
                {"configurable": {"thread_id": f"user:{user.id}"}, "callbacks": [cb]},
            )
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
        reply = _content_to_text(getattr(last, "content", last))

        # Persist a compact memory summary for future retrieval (Chroma).
        # Keep it short to minimize embedding/storage cost.
        summary = f"Usuario: {payload.message.strip()}\nAsistente: {reply.strip()}"
        if len(summary) > 900:
            summary = summary[:900]
        save_context(summary)

        breakdown = _group_usage_breakdown(cb.entries)
        total = cb.totals()
        expense = {"total": total, "breakdown": breakdown}
        return ChatResponse(reply=reply, expense=expense)
    finally:
        reset_agent_label(label_token)
        reset_callbacks(cb_token)
        reset_current_user_id(token)


