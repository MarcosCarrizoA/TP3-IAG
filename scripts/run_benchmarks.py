from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage

# Ensure the repository root is on sys.path when running as a script (python scripts/run_benchmarks.py).
# This makes imports like `from agents import ...` work reliably across platforms.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agents import create_music_agent
from api.callback_context import reset_agent_label, reset_callbacks, set_agent_label, set_callbacks
from api.llm_usage_callback import LLMUsageCallbackHandler
from api.routes.chat import _content_to_text, _group_usage_breakdown  # type: ignore
from api.user_context import reset_current_user_id, set_current_user_id
from bench.mock_context import APIMocks, reset_api_mocks, set_api_mocks
from db.models import User
from db.repositories.playlists import seed_default_playlists_for_user
from db.session import SessionLocal, init_db
from vectorstores import initialize_knowledge_vectorstore, initialize_memory_vectorstore
from vectorstores.stores import reset_vectorstores


def _load_jsonc(path: Path) -> Any:
    raw = path.read_text(encoding="utf-8")
    # strip // comments (simple JSONC)
    raw = re.sub(r"^\s*//.*$", "", raw, flags=re.MULTILINE)
    return json.loads(raw)


def _get_or_create_user_id(username: str) -> int:
    # Keep bench users namespaced to avoid collisions with real app users.
    bench_username = f"bench_{username}"
    with SessionLocal() as db:
        u = db.query(User).filter(User.username == bench_username).first()
        if u is not None:
            # Return a plain scalar to avoid detached ORM instances outside the session.
            return int(u.id)
        from auth.passwords import hash_password

        u = User(username=bench_username, password_hash=hash_password("bench_password"))
        db.add(u)
        db.commit()
        db.refresh(u)
        seed_default_playlists_for_user(db, user_id=int(u.id))
        return int(u.id)


def _memory_dir_for_case(case: dict[str, Any]) -> str:
    base = Path(".bench") / "chroma_memory"
    base.mkdir(parents=True, exist_ok=True)
    if case.get("persistent_memory"):
        # persist across sessions but scoped per user_id
        return str(base / f"persist_{case['user_id']}")
    # isolated per-case
    return str(base / f"case_{case['case_id']}")


def _prepare_memory_dir(case: dict[str, Any]) -> str:
    """
    Ensure the memory directory is in the desired state for this case.

    - persistent_memory=True  -> keep directory (cross-case, cross-run)
    - persistent_memory=False -> wipe directory so the case starts with truly no persistent memory
    """
    d = Path(_memory_dir_for_case(case))
    if not case.get("persistent_memory") and d.exists():
        shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True, exist_ok=True)
    return str(d)


def _thread_id_for_case(case: dict[str, Any], db_user_id: int) -> str:
    if case.get("session_memory"):
        return f"user:{db_user_id}"
    # new session per case (no session memory)
    return f"user:{db_user_id}:case:{case['case_id']}"


def _mocks_for_case(case: dict[str, Any]) -> APIMocks:
    m = case.get("api_mocks") or {}
    return APIMocks(
        location=m.get("location"),
        time=m.get("time"),
        season=m.get("season"),
        weather=m.get("weather"),
        temperature_c=m.get("temperature_c"),
    )


def _print_table(rows: list[dict[str, Any]]) -> None:
    # compact human output
    print("\n=== Benchmark results ===")
    for r in rows:
        exp = r.get("expense") or {}
        total = (exp.get("total") or {}) if isinstance(exp, dict) else {}
        print(
            f"[{r['case_id']}] {r.get('description','')}\n"
            f"  input:  {r['input_message']}\n"
            f"  output: {r['output_message']}\n"
            f"  tokens: input={total.get('input_tokens','-')} output={total.get('output_tokens','-')} total={total.get('total_tokens','-')}\n"
        )


def _summarize_msg(m: Any, *, max_len: int = 240) -> dict[str, Any]:
    try:
        content = getattr(m, "content", None)
    except Exception:
        content = None
    text = _content_to_text(content) if content is not None else ""
    text = (text or "").strip()
    if len(text) > max_len:
        text = text[: max_len - 3] + "..."
    meta_keys: list[str] = []
    for attr in ("additional_kwargs", "response_metadata", "usage_metadata"):
        try:
            v = getattr(m, attr, None)
            if isinstance(v, dict) and v:
                meta_keys.append(attr)
        except Exception:
            pass
    return {"type": type(m).__name__, "preview": text, "meta": meta_keys}


def main() -> None:
    p = argparse.ArgumentParser(description="Run deterministic benchmark cases (no UI).")
    p.add_argument("--cases", default="data/benchmarks/cases.jsonc", help="Path to JSONC cases file")
    p.add_argument("--out", default="data/benchmarks/results.json", help="Output JSON file")
    p.add_argument("--csv", default="", help="Optional output CSV file")
    p.add_argument("--only", default="", help="Comma-separated case ids to run (e.g. C01,C02,C10)")
    p.add_argument("--case-regex", default="", help="Regex to match case_id (e.g. '^C0[1-9]$')")
    p.add_argument("--no-table", action="store_true", help="Do not print a human-readable table to stdout")
    args = p.parse_args()

    cases_path = Path(args.cases)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cases = _load_jsonc(cases_path)
    if not isinstance(cases, list):
        raise SystemExit("cases file must contain a JSON array")

    only_set: set[str] = set()
    if args.only:
        only_set = {c.strip() for c in str(args.only).split(",") if c.strip()}
    case_re = re.compile(args.case_regex) if args.case_regex else None

    # DB tables + vectorstores init
    init_db()
    initialize_knowledge_vectorstore()

    # Agent init once (session isolation is controlled via thread_id per case)
    agent = create_music_agent()

    results: list[dict[str, Any]] = []

    for case in cases:
        if not isinstance(case, dict):
            continue
        case_id = str(case.get("case_id") or "")
        if only_set and case_id not in only_set:
            continue
        if case_re and not case_re.search(case_id):
            continue

        db_user_id = _get_or_create_user_id(str(case.get("user_id") or "u"))
        user_token = set_current_user_id(db_user_id)

        # Per-case vectorstore dir (persistent vs isolated)
        os.environ["CHROMA_MEMORY_DIR"] = _prepare_memory_dir(case)
        reset_vectorstores(reset_memory=True, reset_knowledge=False)
        initialize_memory_vectorstore()

        # Mocks for external APIs/tools
        mocks_token = set_api_mocks(_mocks_for_case(case))

        cb = LLMUsageCallbackHandler()
        cb_token = set_callbacks([cb])
        label_token = set_agent_label("main_agent")

        try:
            messages = [
                SystemMessage(content=agent._system_prompt),
                # NOTE: We intentionally DO NOT auto-inject "memoria relevante" here.
                # The agent can call get_similar_contexts() tool when needed.
                HumanMessage(content=str(case.get("input_message") or "")),
            ]

            response = agent.invoke(
                {"messages": messages},
                {"configurable": {"thread_id": _thread_id_for_case(case, db_user_id)}, "callbacks": [cb]},
            )

            msgs = response.get("messages") or []
            last = msgs[-1] if msgs else None
            reply = _content_to_text(getattr(last, "content", last)) if last is not None else ""

            breakdown = _group_usage_breakdown(cb.entries)
            total = cb.totals()
            expense = {"total": total, "breakdown": breakdown}

            debug: dict[str, Any] | None = None
            if not str(reply).strip():
                tail = msgs[-6:] if len(msgs) >= 6 else msgs
                debug = {
                    "note": "empty_output_message",
                    "messages_tail": [_summarize_msg(m) for m in tail],
                }

            results.append(
                {
                    "case_id": case.get("case_id"),
                    "description": case.get("description"),
                    "user_id": case.get("user_id"),
                    "session_memory": bool(case.get("session_memory")),
                    "persistent_memory": bool(case.get("persistent_memory")),
                    "api_mocks": asdict(_mocks_for_case(case)),
                    "input_message": case.get("input_message"),
                    "output_message": reply,
                    "expense": expense,
                    **({"debug": debug} if debug else {}),
                }
            )
        finally:
            reset_agent_label(label_token)
            reset_callbacks(cb_token)
            reset_api_mocks(mocks_token)
            reset_current_user_id(user_token)

    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.csv:
        csv_path = Path(args.csv)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["case_id", "description", "input_message", "output_message", "input_tokens", "output_tokens", "total_tokens"])
            for r in results:
                total = (r.get("expense") or {}).get("total") or {}
                w.writerow(
                    [
                        r.get("case_id"),
                        r.get("description"),
                        r.get("input_message"),
                        r.get("output_message"),
                        total.get("input_tokens"),
                        total.get("output_tokens"),
                        total.get("total_tokens"),
                    ]
                )

    if not args.no_table:
        _print_table(results)


if __name__ == "__main__":
    main()


