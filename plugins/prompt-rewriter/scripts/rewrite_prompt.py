#!/usr/bin/env python3
"""Rewrite a prompt on demand using Codex."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

PROMPT_GUIDANCE_URL = "https://developers.openai.com/api/docs/guides/prompt-guidance"
LATEST_MODEL_URL = "https://developers.openai.com/api/docs/guides/latest-model"


def detected_target_model(args_target_model: str | None, rewrite_model: str | None) -> str:
    candidates = [
        args_target_model,
        os.environ.get("PROMPT_REWRITER_TARGET_MODEL"),
        os.environ.get("CODEX_MODEL"),
        os.environ.get("OPENAI_MODEL"),
        os.environ.get("MODEL"),
        rewrite_model,
    ]
    for candidate in candidates:
        if candidate and candidate.strip():
            return candidate.strip()
    return "unspecified"


def guidance_section_for_model(model: str) -> str:
    normalized = model.lower()
    if "gpt-5.5" in normalized:
        return "GPT-5.5 prompting guide"
    if "gpt-5.4" in normalized:
        return "GPT-5.4 prompting guide"
    if "gpt-5.3" in normalized and "codex" in normalized:
        return "GPT-5.3 Codex prompting guide"
    if "gpt-5.3" in normalized:
        return "closest GPT-5.3 or GPT-5 series prompting guidance"
    if "gpt-5.2" in normalized:
        return "GPT-5.2 prompting guide"
    if "gpt-5.1" in normalized:
        return "GPT-5.1 prompting guide"
    if "gpt-5" in normalized:
        return "GPT-5 prompting guide, or the current GPT-5.5 guide when upgrading a prompt"
    if "gpt-4.1" in normalized:
        return "GPT-4.1 prompting guide"
    if "gpt-realtime" in normalized:
        return "Realtime prompting guide for the target realtime model"
    return "the current Prompt guidance page, without inventing a model-specific section"


def read_prompt(argv_prompt: list[str]) -> str:
    if argv_prompt:
        return " ".join(argv_prompt).strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Rewrite a prompt for Codex.")
    parser.add_argument("prompt", nargs="*", help="Prompt text to rewrite. Reads stdin when omitted.")
    parser.add_argument("--model", default=os.environ.get("PROMPT_REWRITER_MODEL"), help="Model used to run the rewrite.")
    parser.add_argument("--target-model", default=None, help="Model the rewritten prompt will be used with.")
    parser.add_argument("--effort", default=os.environ.get("PROMPT_REWRITER_REASONING_EFFORT", "low"))
    parser.add_argument("--timeout", type=int, default=int(os.environ.get("PROMPT_REWRITER_TIMEOUT", "90")))
    args = parser.parse_args()

    prompt = read_prompt(args.prompt)
    if not prompt:
        print("No prompt text provided. Pass text as arguments or stdin.", file=sys.stderr)
        return 2

    target_model = detected_target_model(args.target_model, args.model)
    guidance_section = guidance_section_for_model(target_model)

    instruction = f"""You rewrite user prompts for Codex before a coding agent acts.

Target model for the rewritten prompt: {target_model}
Official guidance to prioritize: {guidance_section}

Use live web search to refresh official OpenAI prompt guidance, prioritizing:
- {PROMPT_GUIDANCE_URL}
- {LATEST_MODEL_URL}

Select the model-specific section that matches the target model when it exists. If the target model is unknown or not covered by a named section, use the current Prompt guidance page and do not pretend a model-specific guide exists.

Apply the guidance pragmatically for a coding-agent prompt:
- For GPT-5.5, prefer shorter, outcome-first prompts with success criteria, allowed side effects, evidence rules, and output shape; avoid over-prescribing process unless the path matters.
- For GPT-5.4, preserve stronger multi-step execution, style/tone, structured output contracts, tool persistence, verification loops, and evidence-grounded synthesis.
- For GPT-5.3 Codex, optimize for agentic coding, compaction resilience, long-running autonomy, and concise rollout-friendly instructions.
- For earlier GPT-5 or GPT-4.1 targets, keep more explicit constraints and examples when they materially improve reliability.

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
