---
description: Rewrite a supplied prompt using the local Prompt Rewriter helper.
---

# /rewrite-prompt

Rewrite the supplied prompt and return only the rewritten prompt text.

## Arguments

- `prompt`: prompt text to rewrite. If omitted, ask the user for the prompt text.

## Workflow

1. Resolve the Prompt Rewriter plugin root.
   - Prefer the installed plugin root if the command context exposes it.
   - Otherwise use `codex plugin list --json` to locate the installed `prompt-rewriter` entry.
   - If working from this marketplace checkout, use `plugins/prompt-rewriter`.
2. Run the helper script with the supplied prompt:

```bash
python3 "$PROMPT_REWRITER_PLUGIN_ROOT/scripts/rewrite_prompt.py" -- "$ARGUMENTS"
```

If the prompt is multiline or not safely represented as one argument, pipe it on stdin instead:

```bash
printf '%s' "$PROMPT_TEXT" | python3 "$PROMPT_REWRITER_PLUGIN_ROOT/scripts/rewrite_prompt.py"
```

3. Return the helper stdout as the final answer. Do not add commentary unless the helper fails.

## Guardrails

- Do not execute the rewritten prompt.
- Do not modify files.
- Do not include the original prompt unless the user asks for a comparison.
- If the helper fails, report the failure and stderr concisely.
