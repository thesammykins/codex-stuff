#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
BANNED_TEXT_PATTERNS = (
    "/Users/",
    "op://",
    "OPENAI_API_KEY",
    "sk-",
    "[TODO",
    "TODO:",
)


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc


def validate_semver(version: str, path: Path) -> None:
    if not re.match(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$", version):
        raise ValueError(f"{path}: version is not semver-like: {version}")


def validate_marketplace(data: dict[str, Any]) -> list[Path]:
    if data.get("name") != "codex-stuff":
        raise ValueError("marketplace name must be codex-stuff")
    plugins = data.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        raise ValueError("marketplace must contain at least one plugin")

    plugin_roots: list[Path] = []
    seen: set[str] = set()
    for entry in plugins:
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("plugin entry missing name")
        if name in seen:
            raise ValueError(f"duplicate plugin entry: {name}")
        seen.add(name)

        source = entry.get("source")
        if not isinstance(source, dict):
            raise ValueError(f"{name}: source must be an object")
        if source.get("source") != "local":
            raise ValueError(f"{name}: source.source must be local")
        path = source.get("path")
        if not isinstance(path, str) or not path.startswith("./plugins/"):
            raise ValueError(f"{name}: source.path must start with ./plugins/")
        plugin_root = (ROOT / path[2:]).resolve()
        if not plugin_root.is_relative_to(ROOT.resolve()):
            raise ValueError(f"{name}: source.path escapes marketplace root")
        if not plugin_root.exists():
            raise ValueError(f"{name}: plugin path does not exist: {path}")
        plugin_roots.append(plugin_root)

        policy = entry.get("policy")
        if not isinstance(policy, dict):
            raise ValueError(f"{name}: missing policy")
        if policy.get("installation") not in {"AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"}:
            raise ValueError(f"{name}: invalid installation policy")
        if policy.get("authentication") not in {"ON_INSTALL", "ON_USE"}:
            raise ValueError(f"{name}: invalid authentication policy")
        if not entry.get("category"):
            raise ValueError(f"{name}: missing category")
    return plugin_roots


def validate_plugin(plugin_root: Path) -> None:
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    if not manifest_path.exists():
        raise ValueError(f"{plugin_root}: missing .codex-plugin/plugin.json")
    manifest = load_json(manifest_path)
    if manifest.get("name") != plugin_root.name:
        raise ValueError(f"{manifest_path}: name must match folder name")
    version = manifest.get("version")
    if not isinstance(version, str):
        raise ValueError(f"{manifest_path}: missing version")
    validate_semver(version, manifest_path)
    if not manifest.get("description"):
        raise ValueError(f"{manifest_path}: missing description")

    for key in ("skills", "apps", "mcpServers", "hooks"):
        value = manifest.get(key)
        if isinstance(value, str) and not value.startswith("./"):
            raise ValueError(f"{manifest_path}: {key} path must start with ./")


def scan_text(plugin_roots: list[Path]) -> None:
    for plugin_root in plugin_roots:
        for path in plugin_root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in BANNED_TEXT_PATTERNS:
                if pattern in text:
                    raise ValueError(f"{path}: banned text pattern found: {pattern}")


def main() -> int:
    try:
        data = load_json(MARKETPLACE)
        plugin_roots = validate_marketplace(data)
        for plugin_root in plugin_roots:
            validate_plugin(plugin_root)
        scan_text(plugin_roots)
    except ValueError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1

    print(f"validated {len(plugin_roots)} plugins")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
