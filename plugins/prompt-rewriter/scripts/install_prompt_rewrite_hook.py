#!/usr/bin/env python3
"""Install or verify the bundled Prompt Rewriter Codex hook."""

from __future__ import annotations

import argparse
import ast
import json
import os
import shlex
import shutil
import sys
from pathlib import Path
from typing import Any

EVENTS = ("SessionStart", "UserPromptSubmit")
HOOK_BASENAME = "prompt_rewrite_context.py"


def plugin_root() -> Path:
    return Path(__file__).resolve().parents[1]


def codex_home(value: str | None) -> Path:
    if value:
        return Path(value).expanduser()
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".codex"


def hook_path(root: Path) -> Path:
    return root / "hooks" / HOOK_BASENAME


def hooks_config_path(home: Path) -> Path:
    return home / "hooks.json"


def python_command() -> str:
    configured = os.environ.get("PROMPT_REWRITER_HOOK_PYTHON")
    binary = configured or shutil.which("python3") or sys.executable or "python3"
    return shlex.quote(binary)


def hook_command(path: Path) -> str:
    return f"{python_command()} {shlex.quote(str(path))}"


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"hooks": {}}
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError(f"{path} field 'hooks' must be a JSON object")
    return data


def write_config(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(data, indent=2) + "\n")
    temp_path.replace(path)


def is_prompt_rewriter_hook(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    if entry.get("type") != "command":
        return False
    command = entry.get("command")
    return isinstance(command, str) and HOOK_BASENAME in command


def remove_existing_prompt_rewriter_hooks(groups: list[Any]) -> list[Any]:
    cleaned_groups: list[Any] = []
    for group in groups:
        if not isinstance(group, dict):
            cleaned_groups.append(group)
            continue
        hooks = group.get("hooks")
        if not isinstance(hooks, list):
            cleaned_groups.append(group)
            continue
        kept_hooks = [entry for entry in hooks if not is_prompt_rewriter_hook(entry)]
        if kept_hooks:
            next_group = dict(group)
            next_group["hooks"] = kept_hooks
            cleaned_groups.append(next_group)
    return cleaned_groups


def add_hook_group(config: dict[str, Any], event: str, command: str) -> None:
    hooks = config.setdefault("hooks", {})
    groups = hooks.get(event, [])
    if not isinstance(groups, list):
        raise ValueError(f"hooks.{event} must be a list")
    groups = remove_existing_prompt_rewriter_hooks(groups)
    groups.append({"matcher": "", "hooks": [{"type": "command", "command": command}]})
    hooks[event] = groups


def validate_python_files(root: Path) -> None:
    for path in (hook_path(root), root / "scripts" / "rewrite_prompt.py"):
        ast.parse(path.read_text(), filename=str(path))


def install(args: argparse.Namespace) -> int:
    root = plugin_root()
    home = codex_home(args.codex_home)
    config_path = hooks_config_path(home)
    command = hook_command(hook_path(root))

    validate_python_files(root)
    config = load_config(config_path)
    for event in EVENTS:
        add_hook_group(config, event, command)

    if args.dry_run:
        print(f"Would update {config_path}")
        print(f"Would install command: {command}")
        return 0

    write_config(config_path, config)
    print(f"Installed Prompt Rewriter hook in {config_path}")
    return 0


def configured_commands(config: dict[str, Any], event: str) -> list[str]:
    hooks = config.get("hooks")
    if not isinstance(hooks, dict):
        return []
    groups = hooks.get(event)
    if not isinstance(groups, list):
        return []
    commands: list[str] = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        entries = group.get("hooks")
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict) and entry.get("type") == "command":
                command = entry.get("command")
                if isinstance(command, str):
                    commands.append(command)
    return commands


def verify(args: argparse.Namespace) -> int:
    root = plugin_root()
    home = codex_home(args.codex_home)
    config_path = hooks_config_path(home)
    expected_hook = hook_path(root)
    errors: list[str] = []

    if not expected_hook.exists():
        errors.append(f"Missing hook: {expected_hook}")
    if not (root / "scripts" / "rewrite_prompt.py").exists():
        errors.append("Missing rewrite helper script")
    try:
        validate_python_files(root)
    except SyntaxError as exc:
        errors.append(str(exc))

    try:
        config = load_config(config_path)
    except Exception as exc:
        errors.append(f"Could not read {config_path}: {exc}")
        config = {"hooks": {}}

    expected = str(expected_hook)
    for event in EVENTS:
        commands = configured_commands(config, event)
        if not any(expected in command for command in commands):
            errors.append(f"Missing {event} hook command for {expected_hook}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"Prompt Rewriter hook is installed in {config_path}")
    return 0


def print_config(_args: argparse.Namespace) -> int:
    root = plugin_root()
    command = hook_command(hook_path(root))
    snippet = {
        "hooks": {
            event: [{"matcher": "", "hooks": [{"type": "command", "command": command}]}]
            for event in EVENTS
        }
    }
    print(json.dumps(snippet, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Install or verify the Prompt Rewriter Codex hook.")
    subparsers = parser.add_subparsers(dest="action", required=True)

    install_parser = subparsers.add_parser("install", help="Install the hook into hooks.json.")
    install_parser.add_argument(
        "--codex-home",
        default=None,
        help="Codex home directory. Defaults to CODEX_HOME or the standard Codex home.",
    )
    install_parser.add_argument("--dry-run", action="store_true", help="Show the planned change without writing.")
    install_parser.set_defaults(func=install)

    verify_parser = subparsers.add_parser("verify", help="Verify the hook is configured.")
    verify_parser.add_argument(
        "--codex-home",
        default=None,
        help="Codex home directory. Defaults to CODEX_HOME or the standard Codex home.",
    )
    verify_parser.set_defaults(func=verify)

    snippet_parser = subparsers.add_parser("print-config", help="Print a hooks.json snippet.")
    snippet_parser.set_defaults(func=print_config)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
