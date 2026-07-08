# Model-Specific Prompt Guidance

Prompt Rewriter should use the official OpenAI Prompt guidance page as its source of truth and select the section that matches the target model when one exists.

Reference pages:

- `https://developers.openai.com/api/docs/guides/prompt-guidance`
- `https://developers.openai.com/api/docs/guides/latest-model`

Current guidance checked on 2026-07-08:

- GPT-5.5: shorter, outcome-first prompts; define success criteria, constraints, evidence rules, allowed side effects, and output shape; remove stale process-heavy scaffolding when the exact path does not matter.
- GPT-5.4: stronger multi-step execution, style/tone control, structured output contracts, tool persistence, verification loops, and evidence-grounded synthesis.
- GPT-5.3 Codex: agentic coding, long-running autonomy, compaction resilience, and concise rollout-friendly instructions.
- Earlier GPT-5 and GPT-4.1 targets: keep explicit constraints and examples when they materially improve reliability.

If a target model is unknown or not covered by a named section, use the current Prompt guidance page and avoid inventing model-specific advice.
