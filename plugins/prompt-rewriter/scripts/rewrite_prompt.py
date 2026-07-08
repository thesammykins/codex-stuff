#!/usr/bin/env python3
"""Rewrite a prompt on demand using Codex."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

GUIDE_URL = "https://platform.openai.com/docs/guides/prompt-engineering"


def read_prompt(argv_prompt: list[str]) -> str:
    if argv_prompt:
        return " ".join(argv_prompt).strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Rewrite a prompt for Codex.")
    parser.add_argument("prompt", nargs="*", help="Prompt text to rewrite. Reads stdin when omitted.")
    parser.add_argument("--model", default=os.environ.get("PROMPT_REWRITER_MODEL"))
    parser.add_argument("--effort", default=os.environ.get("PROMPT_REWRITER_REASONING_EFFORT", "low"))
    parser.add_argument("--timeout", type=int, default=int(os.environ.get("PROMPT_REWRITER_TIMEOUT", "90")))
    args = parser.parse_args()

    prompt = read_prompt(args.prompt)
    if not prompt:
        print("No prompt text provided. Pass text as arguments or stdin.", file=sys.stderr)
        return 2

    instruction = f"""You rewrite user prompts for Codex before a coding agent acts.

Use live web search to refresh the official OpenAI prompt engineering guide, prioritizing {GUIDE_URL} or the current official OpenAI prompt guidance page. Apply the guide pragmatically for a coding-agent prompt.

Rewrite the prompt to be clearer, more actionable, and better scoped while preserving the user's intent. Do not add requirements the user did not imply. Keep it concise. Prefer concrete objectives, constraints, deliverables, and verification expectations. Return only the rewritten prompt text, with no preamble, no markdown fence, and no explanation.

Original prompt:
{prompt}
"""

    env = os.environ.copy()
    env["CODEX_PROMPT_REWRITE_DISABLE"] = "1"

    command = [
        "codex",
        "--search",
        "exec",
        "--ephemeral",
        "--config",
        f'model_reasoning_effort="{args.effort}"',
        "--skip-git-repo-check",
        instruction,
    ]
    if args.model:
        command[4:4] = ["--model", args.model]

    result = subprocess.run(
        command,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=args.timeout,
        check=False,
    )

    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        return result.returncode

    print(result.stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
