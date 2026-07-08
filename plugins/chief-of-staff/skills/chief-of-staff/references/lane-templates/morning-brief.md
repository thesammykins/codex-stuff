# Morning Brief Template

Chief of Staff morning brief.

HQ thread: `{{HQ_THREAD_ID}}`. Send the concise brief to that Codex thread using thread tools if available. If thread tools are unavailable, leave the report as the automation final output and say that HQ delivery was unavailable.

Run-window guard:
- Treat `{{TIMEZONE}}` as the only scheduling timezone.
- Only perform the scan on `{{MORNING_DAYS}}` when the current local time is between `{{MORNING_WINDOW}}`.
- If this run starts outside that window, inspect nothing external, do not message HQ, and end with exactly: `{{MORNING_SKIP_STRING}}`

Allowed read-only inputs:
- Calendar agenda and conflicts.
- Recent important inbox threads.
- Relevant project signals from configured project tools.
- Public chat/channel signals only when configured.

Hard safety rules:
- Read-only by default.
- Do not mutate email, chat, calendar, docs, tasks, issues, code, or files.
- Do not inspect secrets or credential material.

Brief format:
1. Top priorities: 3-5 bullets.
2. Calendar: meetings, conflicts, prep needs, and protected time.
3. Inbox: urgent or high-signal items only.
4. Projects: blockers, stale reviews, waiting-on, and deadlines.
5. Suggested actions: review-gated options only.
6. Questions: only if answering them would materially improve the next run.

Keep it compact and operational.

