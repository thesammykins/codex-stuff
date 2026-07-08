# Codex Stuff

Personal and team Codex plugins packaged as a Git-backed marketplace.

## Install

```bash
codex plugin marketplace add thesammykins/codex-stuff --ref main
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
python3 scripts/validate_marketplace.py
```

## Publishing Rules

- Keep plugins generic before publishing.
- Remove absolute local paths, usernames, machine paths, project-private notes, credentials, and repo-specific adapters.
- Put project-specific implementation guidance in the consuming project, not in shared plugin payloads.
- Update `.agents/plugins/marketplace.json` when adding or removing plugins.
- Prefer stable semantic versions in published plugin manifests.
