# Codex Stuff

Reusable Codex plugins packaged as a Git-backed marketplace.

This repo owns plugin packaging only. Fresh-machine installation is orchestrated by [`thesammykins/new-mac`](https://github.com/thesammykins/new-mac), which adds this marketplace and selected plugins for profiles that include `codex-stuff`.

## Install

```bash
codex plugin marketplace add thesammykins/codex-stuff --ref main
codex plugin add arxiv-research@codex-stuff
codex plugin add chief-of-staff@codex-stuff
codex plugin add local-ci-signoff@codex-stuff
codex plugin add prompt-rewriter@codex-stuff
codex plugin add codex-plugin-publisher@codex-stuff
```

After installing or updating a plugin, start a new Codex thread so new skills and plugin metadata are loaded.

## Layout

```text
.agents/plugins/marketplace.json
plugins/<plugin-name>/.codex-plugin/plugin.json
plugins/<plugin-name>/skills/
plugins/<plugin-name>/commands/
scripts/validate_marketplace.py
```

The marketplace follows the Codex Git-backed marketplace guidance: plugin entries point at `./plugins/<plugin-name>` relative to the repository root, and each entry includes installation policy, authentication policy, and category.

## Validate

```bash
mise run check
```

## Publishing Rules

- Keep plugins generic before publishing.
- Remove absolute local paths, usernames, machine paths, project-private notes, credentials, and repo-specific adapters.
- Put project-specific implementation guidance in the consuming project, not in shared plugin payloads.
- Update `.agents/plugins/marketplace.json` when adding or removing plugins.
- Prefer stable semantic versions in published plugin manifests.
