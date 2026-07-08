---
name: local-ci-signoff
description: Design and implement project-local CI signoff workflows for Codex-driven development. Use when a user wants developer-machine CI, gh-signoff or GitHub commit-status based local verification, pre-push validation, local-vs-remote CI lane design, Buildkite/GitHub Actions simplification, or project-specific adoption plans that keep publishing/release builds on remote CI.
---

# Local CI Signoff

## Overview

Use this skill to turn a project's existing validation commands into a local CI signoff workflow. The goal is fast, trusted developer-machine confidence before pushing, while keeping remote CI for final publishing, release builds, protected deployment, and shared audit evidence.

## Workflow

1. Inventory the repo before designing anything.
   - Read existing task surfaces: `mise.toml`, `package.json`, `Makefile`, `justfile`, `pyproject.toml`, `Cargo.toml`, `Package.swift`, `.buildkite/`, `.github/workflows/`, scripts, and docs.
   - Prefer repo-owned commands over new wrappers.
   - Optionally run `python3 scripts/inventory_local_ci.py --root <repo> --format markdown` from this skill to summarize candidates without executing them.

2. Separate lanes by trust boundary.
   - Local signoff: deterministic checks that a developer machine can run before push or merge.
   - Remote CI: publish, upload, notarize, deploy, release, shared secrets, protected signing, long-running matrix, and final evidence.
   - Do not move secrets, App Store Connect upload keys, signing assets, deployment tokens, or production credentials into local signoff.

3. Design a narrow first lane.
   - Start with a single `local-ci` or `signoff` command that runs the existing short confidence path.
   - Require a clean worktree before writing a signoff status.
   - Fail fast and preserve logs under an ignored generated directory such as `.build/local-ci/`.
   - Keep commands serial at first unless the repo already has a safe parallel runner.

4. Decide how signoff is recorded.
   - Prefer `gh-signoff` when the repository uses GitHub and wants branch protection to require local signoff contexts.
   - Use partial signoffs only when they map to meaningful gates such as `hygiene`, `tests`, `ui-smoke`, or `security`.
   - Use direct `gh api /repos/{owner}/{repo}/statuses/{sha}` only when the project needs custom behavior beyond `gh-signoff`.
   - Do not mark success if the repo is dirty, the target commit changed during the run, or any required command was skipped.

5. Keep remote CI as the final publishing authority.
   - Remote CI should still run release-only gates, signed archives, uploads, and deployment checks.
   - If remote CI is reduced, document exactly which checks moved local, which stayed remote, and what branch protection requires.
   - For GitHub required status checks, remember that status/check contexts generally need to have appeared recently before they are selectable in branch protection.

6. Validate the adoption path.
   - Propose a read-only inventory first.
   - Add docs and scripts in a separate implementation step.
   - Run the proposed local lane at least once before recommending branch protection changes.
   - Treat local signoff as a workflow contract, not as an excuse to bypass review or protected release gates.

## Project Output Shape

When asked to apply this skill to a project, produce:

- Current task inventory and existing remote CI summary.
- Proposed local signoff contexts.
- Proposed remote-only contexts.
- Minimal file changes needed later.
- Security and trust boundaries.
- Validation plan and rollback plan.

For implementation plans, write specs first when the change is broad or cross-cutting. Keep the first implementation slice small enough to verify locally before changing branch protection.

## References

- Read `references/local-ci-principles.md` for the source concept and design constraints.
- Read `references/github-signoff.md` when using `gh-signoff` or commit statuses.
- Keep project-specific adapters in the consuming project repository, not in this shared plugin.
