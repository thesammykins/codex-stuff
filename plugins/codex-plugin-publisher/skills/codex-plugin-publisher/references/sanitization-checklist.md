# Sanitization Checklist

Before publishing a plugin to a shared marketplace, verify:

- No absolute home-directory paths.
- No local usernames, machine names, or private worktree paths.
- No dotenv files, API keys, tokens, certificates, private keys, provisioning profiles, or secret-manager URL references.
- No generated caches, logs, session JSONL files, build artifacts, or screenshots with private data.
- No project-specific adapter notes unless the plugin is intentionally project-scoped.
- No stale placeholder markers or internal scratch notes.
- Manifest `author`, `developerName`, descriptions, and prompts are appropriate for other developers to see.
- Manifest `version` is stable semver and not a local cachebuster string.
- Marketplace entry uses a relative `./plugins/<plugin-name>` path inside the marketplace repo.
