---
name: codex-plugin-publisher
description: Add locally built Codex plugins to a Git-backed marketplace. Use when a user wants to publish, sanitize, validate, version, or distribute internal Codex plugins through a repository marketplace such as `.agents/plugins/marketplace.json` with plugin sources under `plugins/`.
---

# Codex Plugin Publisher

## Workflow

1. Inspect the source plugin before copying it.
   - Read `.codex-plugin/plugin.json`, bundled skills, commands, hooks, scripts, `.mcp.json`, and `.app.json`.
   - Identify local paths, usernames, machine-specific paths, secrets, private repo names, customer names, and project-specific adapters.

2. Sanitize the plugin for shared use.
   - Replace personal author metadata with the marketplace publisher.
   - Remove absolute paths and use plugin-relative paths.
   - Remove project-specific references unless the plugin is intentionally scoped to that project.
   - Move project-specific adoption notes into the consuming repo.
   - Check `references/sanitization-checklist.md` before staging changes.

3. Add or update the plugin under `plugins/<plugin-name>/`.
   - Keep `.codex-plugin/plugin.json` present.
   - Keep manifest paths relative to the plugin root and starting with `./`.
   - Use stable semantic versions; avoid local cachebuster versions in Git-published manifests.

4. Update `.agents/plugins/marketplace.json`.
   - Add one entry per plugin under `plugins[]`.
   - Use `source.path: "./plugins/<plugin-name>"` for plugins stored in this repository.
   - Always include `policy.installation`, `policy.authentication`, and `category`.
   - Preserve the marketplace top-level `name` and `interface.displayName`.

5. Validate.
   - Run `python3 scripts/validate_marketplace.py` from the marketplace root.
   - If plugin validation scripts are available and their dependencies are installed, run them too.
   - Search for obvious leaks such as home-directory paths, local usernames, private project names, secret-manager URLs, API-key variable names, token prefixes, dotenv files, and placeholder markers.

6. Commit and push.
   - Use a concise present-tense commit message.
   - After pushing, the marketplace can be added with `codex plugin marketplace add <owner>/<repo> --ref main`.
   - Install plugins with `codex plugin add <plugin-name>@<marketplace-name>`.

## Notes

- Do not publish credentials, generated local caches, logs, session files, or machine-specific config.
- Do not rely on a local personal marketplace as the source of truth once a plugin is Git-published.
- For changes to an installed plugin, update the Git source, push it, run `codex plugin marketplace upgrade <marketplace-name>`, then reinstall or update the plugin in a new thread.
