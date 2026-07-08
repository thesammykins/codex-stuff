---
name: chief-of-staff
description: Set up or maintain Codex-native chief-of-staff automations, including a pinned HQ thread, recurring read-only lanes, local-time run-window guards, no-noise reporting, and private profile integration.
---

# Chief of Staff

Use this skill when the user wants Codex to act as a recurring chief of staff, set up daily or weekly operational scans, route findings into a durable HQ thread, or port an existing setup to another machine or account.

## Default Shape

Keep the system Codex-native:

1. Create or reuse one visible HQ Codex thread.
2. Pin and clearly title the HQ thread.
3. Create recurring cron automations with `automation_update` when the tool is available.
4. Keep each automation read-only until the user explicitly grants stronger authority.
5. Send messages to HQ only for meaningful findings.
6. Treat worker automation threads as disposable.
7. Keep personal profile data in a private profile plugin or user-provided values, not in this public plugin.

If the current thread does not expose automation or thread tools, explain what is missing and provide copy-paste-ready prompts or commands instead of inventing a sidecar system.

## Profile Values

Before creating or updating automations, resolve these values from the user, an installed private profile plugin, or existing saved automation state:

- `profile_name`
- `timezone`
- `hq_thread_id`
- `workspace_root`
- `codex_home`
- `root_guidance_path`
- allowed connectors and explicitly disallowed surfaces
- lane schedules and local run windows
- preferred models and reasoning effort
- no-noise policy

Never put secrets, tokens, private keys, passwords, or `.env` data into automation prompts or tracked files. If a value is sensitive and needed by GitHub-hosted agents, store it as a GitHub secret by name and reference only the secret name in tracked files.

## Automation Rules

- For `automation_update` create calls, do not pass a caller-selected `id`; let Codex create the automation identity.
- Use future `DTSTART` values. Avoid schedules that immediately trigger catch-up runs.
- Cron scheduling can be surprising across timezones, so every automation prompt must start with a local-time run-window guard.
- If a run starts outside its allowed local window, it must inspect no external systems and send no HQ message.
- Out-of-window runs should end with the lane's exact skip string.
- Read-only lanes may read allowed connectors, summarize, and propose actions, but must not mutate email, Slack, calendar, docs, tasks, issues, code, or files.
- Suppress repeat reports unless there is new material information, a deadline is closer, or priority has changed.

## Recommended Lanes

Start with the smallest useful set:

- Morning brief: calendar, inbox, project, and public-channel signals for the operating day.
- Inbox urgency scan: recent Gmail only, hourly or work-window cadence, urgent/high-signal items only.
- Project blockers scan: Linear/GitHub/Notion/Drive blockers, stale reviews, waiting-on, and decision points.
- Weekly research scout: credible AI/workflow research mapped to concrete Codex or skill improvements.

Use templates from `references/lane-templates/` and safety rules from `references/safety.md`.

## Setup Flow

1. Inspect existing Codex state first: current marketplaces, installed plugins, existing automations, and any existing HQ thread.
2. If no HQ thread exists, create one with a clear title and pin it.
3. Fill `references/profile-template.toml` with non-secret profile values, or read equivalent values from a private profile plugin.
4. Create or update lane prompts from the templates.
5. Validate saved automation state when possible.
6. Start a new Codex thread after installing or updating plugins so new skills are loaded.

## Maintenance Flow

When changing an existing system:

- Use read-only discovery first.
- Keep edits lane-scoped.
- Preserve working skip strings and local-time guards.
- If confidence is low, propose a patch or profile change instead of mutating the automation.
- Do not broaden connector access while fixing a schedule or prompt bug.

