# AGENTS.md - Codex Stuff

## Scope

This repo packages reusable Codex plugins as a Git-backed marketplace. It does not own machine bootstrap, dotfiles, or skill installation policy.

## Rules

- Keep plugin payloads generic and reusable.
- Do not include local absolute paths, credentials, project-private notes, or machine-specific adapters.
- Update `.agents/plugins/marketplace.json` when adding or removing plugins.
- Validate with `mise run check` after plugin metadata changes.
- Let `thesammykins/new-mac` handle installation on a Mac.

