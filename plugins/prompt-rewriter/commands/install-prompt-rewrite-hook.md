---
description: Install or verify the optional first-prompt Prompt Rewriter hook.
---

# /install-prompt-rewrite-hook

Install the bundled Prompt Rewriter hook into the active Codex home, or verify that it is already configured.

The hook rewrites the first user prompt after a new Codex session starts. Later turns are rewritten only when the prompt starts with `/prompt-rewrite`, `/prw`, or `//rewrite`.

## Workflow

1. Resolve the Prompt Rewriter plugin root.
   - Prefer the installed plugin root if the command context exposes it.
   - Otherwise use `codex plugin list --json` to locate the installed `prompt-rewriter` entry.
   - If working from this marketplace checkout, use `plugins/prompt-rewriter`.
2. Preview the configuration change:

```bash
python3 "$PROMPT_REWRITER_PLUGIN_ROOT/scripts/install_prompt_rewrite_hook.py" install --dry-run
```

3. Install the hook when the user wants the prompt rewrite hook enabled:

```bash
python3 "$PROMPT_REWRITER_PLUGIN_ROOT/scripts/install_prompt_rewrite_hook.py" install
```

4. Verify the hook configuration:

```bash
python3 "$PROMPT_REWRITER_PLUGIN_ROOT/scripts/install_prompt_rewrite_hook.py" verify
```

5. Start a new Codex thread so the first-prompt behavior can run from a fresh session.

## Behavior

- The installer updates the active Codex `hooks.json` with `SessionStart` and `UserPromptSubmit` command hooks.
- Existing Prompt Rewriter hook commands are replaced so the hook does not run twice.
- The plugin manifest does not declare hooks directly because hook activation is handled by the installer.
- Set `CODEX_PROMPT_REWRITE_MODEL` to choose the model used for rewriting.
- Set `CODEX_PROMPT_REWRITE_TARGET_MODEL` to choose the model family the rewritten prompt should target.
- Set `CODEX_PROMPT_REWRITE_DISABLE=1` to disable the hook for nested Codex calls.

## Guardrails

- Do not execute the rewritten prompt during installation.
- Do not print unrelated hook commands from the user's hook configuration.
- If installation writes outside the current workspace, get approval before running the installer.
