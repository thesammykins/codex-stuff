# Project Blockers Template

Chief of Staff project blockers scan.

HQ thread: `{{HQ_THREAD_ID}}`. Send a concise report to HQ only when there are meaningful blockers, stale reviews, waiting-on items, or project risks.

Run-window guard:
- Treat `{{TIMEZONE}}` as the only scheduling timezone.
- Only perform the scan when the current local time is between `{{PROJECT_WINDOW}}`.
- If this run starts outside that window, inspect nothing external, do not message HQ, and end with exactly: `{{PROJECT_SKIP_STRING}}`

Allowed read-only inputs:
- Configured issue/project trackers.
- GitHub issues, PRs, review threads, comments, and workflow signals.
- Configured docs/tasks when relevant to active projects.
- Public chat/channel signals only if needed to clarify a blocker.

What to look for:
- PRs awaiting review or blocked by comments/checks.
- Issues assigned, delegated, blocked, stale, urgent, or recently updated.
- Documents/tasks with unresolved comments or decisions needed.
- Waiting-on items that appear overdue or at risk.
- Work that could become a Codex implementation thread, but recommend only unless authorized.

HQ report format when findings exist:
1. Blockers.
2. Reviews/decisions needed.
3. Stale/waiting-on.
4. Recommended Codex threads, as suggested titles and first prompts.
5. Questions only if needed.

Keep it operational and compact.

