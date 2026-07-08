# Safety Rules

- Check the configured local run window before reading external systems.
- If outside the window, inspect nothing external and do not message HQ.
- Keep all lanes read-only until the user explicitly grants write authority.
- Do not send email, draft email, archive email, label email, post Slack messages, edit calendar events, edit docs, update issues, create tasks, or modify files from default lanes.
- Do not read, quote, summarize, or reference `.env` files, credentials, private keys, tokens, password stores, browser profiles, or authentication material.
- Slack public channels are allowed only when configured. Private channels, DMs, and group DMs require explicit user authorization.
- Prefer fewer, higher-signal findings over broad digests.
- If the automation tool is unavailable, produce a copy-paste setup plan instead of building an external scheduler.

