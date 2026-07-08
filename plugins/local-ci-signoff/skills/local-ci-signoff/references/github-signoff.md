# GitHub Signoff Notes

## Preferred Tool

`basecamp/gh-signoff` is a GitHub CLI extension for local CI signoff. It records a successful commit status after local checks pass and can install required signoff protection for a branch.

Typical manual setup:

```bash
gh extension install basecamp/gh-signoff
gh signoff
gh signoff install
```

Partial signoffs can represent separate contexts:

```bash
gh signoff hygiene tests ui-smoke
gh signoff install hygiene tests ui-smoke
gh signoff status
```

## Direct Commit Status Alternative

Use direct `gh api` only if the project needs custom status names, richer descriptions, or a wrapper that must not depend on the extension.

Required safeguards:

- verify `git status --porcelain` is empty before status success;
- capture `git rev-parse HEAD` before and after checks and fail if it changes;
- post only to the current commit SHA;
- use stable context names such as `local/signoff`, `local/hygiene`, or `local/ui-smoke`;
- never post success for optional, skipped, or manually bypassed checks.

## Branch Protection Caveats

GitHub required status checks can block merges, but the contexts need to exist before they are convenient to select in branch protection. Run the signoff at least once on the target repository before configuring the branch rule.

Anyone with sufficient repository write access may be able to set commit statuses. Treat local signoff as an engineering workflow and merge gate, not as a high-assurance security boundary.
