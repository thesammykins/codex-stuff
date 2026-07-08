#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    tomllib = None  # type: ignore[assignment]


TASK_KEYWORDS = (
    "ci",
    "check",
    "doctor",
    "format",
    "hygiene",
    "lint",
    "metadata",
    "quick",
    "smoke",
    "test",
    "typecheck",
    "verify",
)

REMOTE_ONLY_KEYWORDS = (
    "archive",
    "deploy",
    "notar",
    "publish",
    "release",
    "sign",
    "testflight",
    "upload",
)


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def read_toml(path: Path) -> dict[str, Any]:
    if tomllib is None:
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def classify(name: str, command: str) -> str:
    name_text = name.lower()
    command_text = command.lower()
    text = f"{name_text} {command_text}"
    if any(keyword in name_text for keyword in TASK_KEYWORDS):
        return "local-candidate"
    if "--tests" in command_text or " test" in command_text:
        return "local-candidate"
    if any(keyword in text for keyword in REMOTE_ONLY_KEYWORDS):
        return "remote-only-candidate"
    if any(keyword in text for keyword in TASK_KEYWORDS):
        return "local-candidate"
    return "uncategorized"


def collect_mise(root: Path) -> list[dict[str, str]]:
    data = read_toml(root / "mise.toml")
    tasks = data.get("tasks", {})
    collected: list[dict[str, str]] = []
    if isinstance(tasks, dict):
        for name, value in sorted(tasks.items()):
            command = ""
            description = ""
            if isinstance(value, dict):
                run = value.get("run", "")
                command = run if isinstance(run, str) else " ".join(str(item) for item in run)
                description = str(value.get("description", ""))
            elif isinstance(value, str):
                command = value
            collected.append(
                {
                    "source": "mise.toml",
                    "name": name,
                    "command": command,
                    "description": description,
                    "classification": classify(name, command),
                }
            )
    return collected


def collect_package_json(root: Path) -> list[dict[str, str]]:
    data = read_json(root / "package.json")
    scripts = data.get("scripts", {})
    collected: list[dict[str, str]] = []
    if isinstance(scripts, dict):
        for name, command in sorted(scripts.items()):
            command_text = str(command)
            collected.append(
                {
                    "source": "package.json",
                    "name": name,
                    "command": command_text,
                    "description": "",
                    "classification": classify(name, command_text),
                }
            )
    return collected


def collect_makefile(root: Path) -> list[dict[str, str]]:
    path = root / "Makefile"
    if not path.exists():
        return []
    pattern = re.compile(r"^([A-Za-z0-9_.-]+):(?:\s|$)")
    collected: list[dict[str, str]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            match = pattern.match(line)
            if match and not match.group(1).startswith("."):
                name = match.group(1)
                collected.append(
                    {
                        "source": "Makefile",
                        "name": name,
                        "command": f"make {name}",
                        "description": "",
                        "classification": classify(name, f"make {name}"),
                    }
                )
    except OSError:
        return []
    return collected


def collect_buildkite(root: Path) -> list[str]:
    pipeline = root / ".buildkite" / "pipeline.yml"
    if not pipeline.exists():
        return []
    try:
        text = pipeline.read_text(encoding="utf-8")
    except OSError:
        return []
    return sorted(set(re.findall(r"key:\s*[\"']?([A-Za-z0-9_.-]+)", text)))


def inventory(root: Path) -> dict[str, Any]:
    tasks = collect_mise(root) + collect_package_json(root) + collect_makefile(root)
    return {
        "root": str(root),
        "tasks": tasks,
        "buildkite_steps": collect_buildkite(root),
        "local_candidates": [task for task in tasks if task["classification"] == "local-candidate"],
        "remote_only_candidates": [task for task in tasks if task["classification"] == "remote-only-candidate"],
    }


def render_markdown(data: dict[str, Any]) -> str:
    lines = [f"# Local CI Inventory", "", f"Root: `{data['root']}`", ""]
    for heading, key in (
        ("Local Candidates", "local_candidates"),
        ("Remote-Only Candidates", "remote_only_candidates"),
        ("All Detected Tasks", "tasks"),
    ):
        lines.extend([f"## {heading}", ""])
        items = data.get(key, [])
        if not items:
            lines.extend(["No tasks detected.", ""])
            continue
        for task in items:
            description = f" - {task['description']}" if task.get("description") else ""
            lines.append(f"- `{task['name']}` from `{task['source']}`: `{task['command']}`{description}")
        lines.append("")
    steps = data.get("buildkite_steps", [])
    if steps:
        lines.extend(["## Buildkite Steps", ""])
        lines.extend(f"- `{step}`" for step in steps)
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory repo tasks for local CI signoff design.")
    parser.add_argument("--root", default=".", help="Repository root to inspect.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()

    data = inventory(Path(args.root).resolve())
    if args.format == "markdown":
        print(render_markdown(data))
    else:
        print(json.dumps(data, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
