# Weekly Research Scout Template

Weekly AI research-to-practice scout.

HQ thread: `{{HQ_THREAD_ID}}`. Send the weekly memo to HQ when there are credible, actionable findings.

Run-window guard:
- Treat `{{TIMEZONE}}` as the only scheduling timezone.
- Only perform the research scout when the current local time is within `{{RESEARCH_WINDOW}}`.
- If this run starts outside that window, inspect nothing external, do not spawn threads, do not message HQ, and end with exactly: `{{RESEARCH_SKIP_STRING}}`

Purpose:
- Review recent LLM/AI research and identify practical improvements for Codex workflows, local skills, agent guidance, automation prompts, and evaluation habits.

Research guidance:
- Prefer installed research plugins or available paper-search tools.
- Use source links only when obtained from tools/search.
- Focus on concrete workflow implications, not broad literature coverage.

Local audit target:
- Inspect `{{ROOT_GUIDANCE_PATH}}` only when inside the run window and permitted by the profile.
- Compare credible findings to current guidance and propose edits without applying them unless the lane has explicit write authority.

Expected output:
1. Research shortlist: 5-10 items with source link, one-line finding, and why it matters.
2. Practical implications ranked by usefulness.
3. Guidance audit proposals.
4. Suggested spawned task threads or copy-paste prompts.
5. Noise control: findings intentionally ignored.

Keep the HQ memo concise and useful.

