---
description: Rewrite a supplied prompt using the local Prompt Rewriter helper.
---

# /rewrite-prompt

Rewrite the supplied prompt and return only the rewritten prompt text.

## Arguments

- `prompt`: prompt text to rewrite. If omitted, ask the user for the prompt text.
- `--target-model <model>`: optional model the rewritten prompt is for, such as `gpt-5.5`, `gpt-5.4`, or `gpt-5.3-codex`.
- `--model <model>`: optional model used to perform the rewrite.

## Workflow

1. Resolve the Prompt Rewriter plugin root.
   - Prefer the installed plugin root if the command context exposes it.
   - Otherwise use `codex plugin list --json` to locate the installed `prompt-rewriter` entry.
   - If working from this marketplace checkout, use `plugins/prompt-rewriter`.
2. Run the helper script with the supplied prompt:

```bash
python3 "$PROMPT_REWRITER_PLUGIN_ROOT/scripts/rewrite_prompt.py" --target-model "$TARGET_MODEL" -- "$ARGUMENTS"
```

If the prompt is multiline or not safely represented as one argument, pipe it on stdin instead:

```bash
printf '%s' "$PROMPT_TEXT" | python3 "$PROMPT_REWRITER_PLUGIN_ROOT/scripts/rewrite_prompt.py" --target-model "$TARGET_MODEL"
```

3. Return the helper stdout as the final answer. Do not add commentary unless the helper fails.

## Model Guidance

- Use the target model if the user names one.
- If the target model is omitted, let the helper infer it from `PROMPT_REWRITER_TARGET_MODEL`, `CODEX_MODEL`, `OPENAI_MODEL`, `MODEL`, or the rewrite model.
- The helper prioritizes the official OpenAI Prompt guidance page and selects the matching model section when available, including GPT-5.5, GPT-5.4, GPT-5.3 Codex, earlier GPT-5 sections, and GPT-4.1.

## Guardrails

- Do not execute the rewritten prompt.
- Do not modify files.
- Do not include the original prompt unless the user asks for a comparison.
- If the helper fails, report the failure and stderr concisely.
