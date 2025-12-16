from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any, Optional

from langchain_core.callbacks import BaseCallbackHandler

from api.callback_context import get_agent_label


def _normalize_usage(u: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}

    # Common normalized keys
    if "input_tokens" in u:
        out["input_tokens"] = int(u["input_tokens"])
    if "output_tokens" in u:
        out["output_tokens"] = int(u["output_tokens"])
    if "total_tokens" in u:
        out["total_tokens"] = int(u["total_tokens"])

    # Gemini raw keys
    if "promptTokenCount" in u and "input_tokens" not in out:
        out["input_tokens"] = int(u["promptTokenCount"])
    if "candidatesTokenCount" in u and "output_tokens" not in out:
        out["output_tokens"] = int(u["candidatesTokenCount"])
    if "totalTokenCount" in u and "total_tokens" not in out:
        out["total_tokens"] = int(u["totalTokenCount"])

    return out


def _extract_usage_from_llm_result(result: Any) -> Optional[dict[str, Any]]:
    """
    Best-effort extraction from a LangChain LLMResult / ChatResult.
    This varies across providers.
    """
    # 1) llm_output
    llm_output = getattr(result, "llm_output", None)
    if isinstance(llm_output, dict) and llm_output:
        for key in ("usage_metadata", "token_usage", "usage", "usageMetadata"):
            inner = llm_output.get(key)
            if isinstance(inner, dict) and inner:
                norm = _normalize_usage(inner)
                if norm:
                    return norm
        norm = _normalize_usage(llm_output)
        if norm:
            return norm

    # 2) generations -> message metadata
    generations = getattr(result, "generations", None)
    if generations:
        try:
            first = generations[0][0]
            msg = getattr(first, "message", None) or getattr(first, "text", None)
            for attr in ("usage_metadata", "response_metadata", "additional_kwargs"):
                meta = getattr(msg, attr, None) if msg is not None else None
                if isinstance(meta, dict) and meta:
                    inner = meta.get("usage_metadata") or meta.get("token_usage") or meta.get("usage") or meta
                    if isinstance(inner, dict) and inner:
                        norm = _normalize_usage(inner)
                        if norm:
                            return norm
        except Exception:
            pass

    return None


@dataclass
class UsageEntry:
    agent: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    model: Optional[str] = None


class LLMUsageCallbackHandler(BaseCallbackHandler):
    """
    Captures token usage for ALL LLM calls in a request.
    Overhead is tiny: it just reads metadata at the end of each call.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self.entries: list[dict[str, Any]] = []

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:  # type: ignore[override]
        usage = _extract_usage_from_llm_result(response)
        if not usage:
            return

        agent = get_agent_label() or "agent"
        model = None
        try:
            inv = kwargs.get("invocation_params") or {}
            if isinstance(inv, dict):
                model = inv.get("model") or inv.get("model_name")
        except Exception:
            pass

        entry: dict[str, Any] = {"agent": agent, **usage}
        if model:
            entry["model"] = str(model)

        with self._lock:
            self.entries.append(entry)

    def totals(self) -> dict[str, int]:
        total_in = 0
        total_out = 0
        total_all = 0
        with self._lock:
            for e in self.entries:
                if isinstance(e.get("input_tokens"), int):
                    total_in += int(e["input_tokens"])
                if isinstance(e.get("output_tokens"), int):
                    total_out += int(e["output_tokens"])
                if isinstance(e.get("total_tokens"), int):
                    total_all += int(e["total_tokens"])
        out: dict[str, int] = {}
        out["input_tokens"] = total_in
        out["output_tokens"] = total_out
        out["total_tokens"] = total_all
        return out


