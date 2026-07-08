# Inbox Urgency Template

Chief of Staff inbox urgency scan.

HQ thread: `{{HQ_THREAD_ID}}`. Send a message to HQ only when there are meaningful urgent or high-signal findings.

Run-window guard:
- Treat `{{TIMEZONE}}` as the only scheduling timezone.
- Only perform the scan on `{{INBOX_DAYS}}` when the current local time is between `{{INBOX_WINDOW}}`.
- If this run starts outside that window, inspect nothing external, do not message HQ, and end with exactly: `{{INBOX_SKIP_STRING}}`

Primary input:
- Gmail or the configured inbox connector only, unless a specific message clearly points to calendar/project context needed to understand urgency.

Triage guidance:
- Focus on direct asks, time-sensitive requests, meeting changes, operational blockers, access issues, review requests, and high-priority senders when evident.
- Ignore newsletters, promotions, automated marketing, and generic notifications unless clearly urgent.
- Read enough of a thread to avoid hallucinating context.
- Suppress repeat reports unless there is new material information.

HQ report format when findings exist:
1. Urgent now.
2. Suggested reply/action.
3. Waiting-on/follow-up.
4. Questions only if needed.

Keep it short.

