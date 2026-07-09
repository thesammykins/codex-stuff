#!/usr/bin/env python3
"""Rewrite the first user prompt of a Codex session as hook context."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

EVENT_SESSION_START = "SessionStart"
EVENT_USER_PROMPT = "UserPromptSubmit"
EVENT_KEYS = ("hook_event_name", "hookEventName", "event_name")

FORCE_PREFIXES = ("/prompt-rewrite ", "/prw ", "//rewrite ")


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


REWRITE_MODEL = (
    os.environ.get("CODEX_PROMPT_REWRITE_MODEL")
    or os.environ.get("PROMPT_REWRITER_MODEL")
    or "gpt-5.4-mini"
)
TARGET_MODEL = os.environ.get("CODEX_PROMPT_REWRITE_TARGET_MODEL") or os.environ.get(
    "PROMPT_REWRITER_TARGET_MODEL"
)
TIMEOUT_SECONDS = env_int("CODEX_PROMPT_REWRITE_TIMEOUT", 90)
MAX_PROMPT_CHARS = env_int("CODEX_PROMPT_REWRITE_MAX_CHARS", 12000)
PENDING_WAIT_SECONDS = env_float("CODEX_PROMPT_REWRITE_PENDING_WAIT", 2.0)
PENDING_TTL_SECONDS = env_float("CODEX_PROMPT_REWRITE_PENDING_TTL", 600.0)
SEEN_TTL_SECONDS = env_float("CODEX_PROMPT_REWRITE_SEEN_TTL", 30 * 24 * 60 * 60.0)
MAX_TRACKED_SESSIONS = env_int("CODEX_PROMPT_REWRITE_MAX_SESSIONS", 1000)


def plugin_root() -> Path:
    configured = os.environ.get("PROMPT_REWRITER_PLUGIN_ROOT")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1]


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".codex"


def state_file() -> Path:
    configured = os.environ.get("CODEX_PROMPT_REWRITE_STATE_FILE")
    if configured:
        path = Path(configured).expanduser()
    else:
        path = codex_home() / "hooks" / "prompt-rewrite-state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def lock_file() -> Path:
    configured = os.environ.get("CODEX_PROMPT_REWRITE_LOCK_FILE")
    if configured:
        path = Path(configured).expanduser()
    else:
        path = state_file().with_suffix(".lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def event_name(payload: dict[str, Any]) -> str | None:
    for key in EVENT_KEYS:
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def session_id_from(payload: dict[str, Any]) -> str | None:
    direct = payload.get("session_id")
    if isinstance(direct, str) and direct:
        return direct
    session = payload.get("session")
    if isinstance(session, dict):
        nested = session.get("id")
        if isinstance(nested, str) and nested:
            return nested
    env_session = os.environ.get("CODEX_SESSION_ID")
    if env_session:
        return env_session
    return None


def session_key(session_id: str) -> str:
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()


def load_state(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError:
        return {"sessions": {}}
    except Exception:
        return {"sessions": {}}
    if not isinstance(data, dict):
        return {"sessions": {}}
    sessions = data.get("sessions")
    if not isinstance(sessions, dict):
        data["sessions"] = {}
    return data


def prune_state(state: dict[str, Any], now: float) -> None:
    sessions = state.setdefault("sessions", {})
    if not isinstance(sessions, dict):
        state["sessions"] = {}
        return

    for key, record in list(sessions.items()):
        if not isinstance(record, dict):
            sessions.pop(key, None)
            continue
        status = record.get("status")
        updated_at = float(record.get("updated_at", 0) or 0)
        age = now - updated_at
        if status == "pending" and age > PENDING_TTL_SECONDS:
            sessions.pop(key, None)
        elif status == "seen" and age > SEEN_TTL_SECONDS:
            sessions.pop(key, None)

    if len(sessions) > MAX_TRACKED_SESSIONS:
        sorted_items = sorted(
            sessions.items(),
            key=lambda item: float(item[1].get("updated_at", 0) or 0)
            if isinstance(item[1], dict)
            else 0,
        )
        for key, _record in sorted_items[: len(sessions) - MAX_TRACKED_SESSIONS]:
            sessions.pop(key, None)


def mutate_state(mutator: Callable[[dict[str, Any], float], Any]) -> Any:
    state_path = state_file()
    lock_path = lock_file()
    with lock_path.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        now = time.time()
        state = load_state(state_path)
        prune_state(state, now)
        result = mutator(state, now)
        temp_path = state_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(state, separators=(",", ":")) + "\n")
        temp_path.replace(state_path)
        return result


def mark_session_pending(session_id: str) -> None:
    key = session_key(session_id)

    def update(state: dict[str, Any], now: float) -> None:
        sessions = state.setdefault("sessions", {})
        sessions[key] = {"status": "pending", "updated_at": now}

    mutate_state(update)


def consume_first_prompt_slot(session_id: str) -> bool:
    key = session_key(session_id)
    deadline = time.monotonic() + PENDING_WAIT_SECONDS

    while True:
        consumed = _consume_first_prompt_slot_once(key)
        if consumed:
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.1)


def _consume_first_prompt_slot_once(key: str) -> bool:
    def update(state: dict[str, Any], now: float) -> bool:
        sessions = state.setdefault("sessions", {})
        record = sessions.get(key)
        if not isinstance(record, dict) or record.get("status") != "pending":
            return False
        sessions[key] = {"status": "seen", "updated_at": now}
        return True

    return bool(mutate_state(update))


def prompt_from_payload(payload: dict[str, Any]) -> str:
    prompt = payload.get("prompt")
    if isinstance(prompt, str):
        return prompt

    message = payload.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return content

    messages = payload.get("messages")
    if isinstance(messages, list):
        for item in reversed(messages):
            if not isinstance(item, dict) or item.get("role") != "user":
                continue
            content = item.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = [part.get("text", "") for part in content if isinstance(part, dict)]
                text = "\n".join(part for part in parts if part)
                if text:
                    return text

    return ""


def strip_force_prefix(prompt: str) -> tuple[bool, str]:
    stripped = prompt.lstrip()
    leading = prompt[: len(prompt) - len(stripped)]
    lowered = stripped.lower()
    for prefix in FORCE_PREFIXES:
        if lowered.startswith(prefix):
            return True, leading + stripped[len(prefix) :].lstrip()
    return False, prompt


def rewrite_prompt(prompt: str, payload: dict[str, Any]) -> str:
    helper = plugin_root() / "scripts" / "rewrite_prompt.py"
    if not helper.exists():
        raise RuntimeError(f"Missing bundled prompt rewriter helper: {helper}")

    rewrite_input = prompt[:MAX_PROMPT_CHARS]
    env = os.environ.copy()
    env["CODEX_PROMPT_REWRITE_DISABLE"] = "1"

    command = [
        sys.executable or "python3",
        str(helper),
        "--model",
        REWRITE_MODEL,
        "--timeout",
        str(TIMEOUT_SECONDS),
    ]
    if TARGET_MODEL:
        command.extend(["--target-model", TARGET_MODEL])

    cwd = payload.get("cwd")
    run_cwd = cwd if isinstance(cwd, str) and Path(cwd).is_dir() else None
    result = subprocess.run(
        command,
        cwd=run_cwd,
        env=env,
        input=rewrite_input,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=TIMEOUT_SECONDS + 10,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or f"rewrite helper exited with {result.returncode}"
        raise RuntimeError(message)
    return result.stdout.strip()


def emit_context(text: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": EVENT_USER_PROMPT,
                    "additionalContext": text,
                }
            }
        )
    )


def emit_rewrite_context(prompt: str, payload: dict[str, Any], forced: bool) -> int:
    try:
        rewritten = rewrite_prompt(prompt, payload)
    except Exception as exc:
        emit_context(f"Prompt rewrite hook failed: {exc}")
        return 0

    if not rewritten:
        return 0

    source = "An explicit prompt rewrite prefix" if forced else "The prompt rewrite hook"
    emit_context(
        f"{source} rewrote the user's prompt. Treat the rewritten prompt below as the user's intended request, "
        "while preserving any later user corrections.\n\n"
        f"Rewritten prompt:\n{rewritten}"
    )
    return 0


def handle_session_start(payload: dict[str, Any]) -> int:
    session_id = session_id_from(payload)
    if session_id:
        mark_session_pending(session_id)
    return 0


def handle_user_prompt_submit(payload: dict[str, Any]) -> int:
    prompt = prompt_from_payload(payload)
    if not prompt.strip():
        return 0

    forced, prompt_to_rewrite = strip_force_prefix(prompt)
    if forced:
        return emit_rewrite_context(prompt_to_rewrite, payload, forced=True)

    session_id = session_id_from(payload)
    if not session_id or not consume_first_prompt_slot(session_id):
        return 0
    return emit_rewrite_context(prompt, payload, forced=False)


def main() -> int:
    if os.environ.get("CODEX_PROMPT_REWRITE_DISABLE") == "1":
        return 0

    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    if not isinstance(payload, dict):
        return 0

    name = event_name(payload)
    if name == EVENT_SESSION_START:
        return handle_session_start(payload)
    if name == EVENT_USER_PROMPT:
        return handle_user_prompt_submit(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
