# Local CI Principles

## Concept

The DHH/37signals idea is to move ordinary integration confidence back to modern developer machines when the project size and team shape allow it. The practical form is:

- run the same checks locally that remote CI would normally run for everyday changes;
- record a green commit status after those checks pass;
- require that status for merge if the team wants enforcement;
- keep remote CI for release, publish, deployment, secrets, and expensive shared evidence.

This is not anti-CI. It is a lane split: local machines handle routine confidence; remote systems handle protected, shared, and publishing work.

## Design Constraints

- Keep the workflow repo-owned. Commands should live in project scripts, `mise`, `just`, `make`, package scripts, or equivalent.
- Do not depend on a developer remembering a checklist by hand.
- Do not require global installs unless the user explicitly accepts them. Prefer documenting optional tools such as `gh extension install basecamp/gh-signoff`.
- Do not write success status unless all required local commands ran against the exact commit being signed off.
- Do not hide skipped checks. A skipped command is a failure unless the local CI config explicitly marks it optional.
- Preserve logs locally, but do not commit generated logs.
- Keep remote CI for release signing, App Store/TestFlight upload, deployment, production credentials, and cross-machine reproducibility checks.
- Prefer one boring command over a bespoke orchestrator until real duplication appears.

## Good Candidate Checks

- lint, formatting, typecheck, shellcheck, metadata validation;
- unit tests and integration tests that run reliably on a developer machine;
- simulator/browser smoke tests that use bounded local devices;
- security scans that do not need protected credentials;
- project generation drift checks.

## Poor Candidate Checks

- signing or notarization that requires protected secrets;
- production deploys or App Store uploads;
- long multi-platform matrices;
- jobs requiring isolated infrastructure for trust reasons;
- flaky suites that are only diagnosable through centralized artifacts.

## Adoption Sequence

1. Inventory existing commands and remote jobs.
2. Choose the smallest useful local lane.
3. Add a repo-owned command that runs the lane and saves logs.
4. Optionally install and use `gh-signoff` for commit status.
5. Run the lane manually for a few changes.
6. Only then consider required status checks or remote CI simplification.
7. Keep a remote final gate for publishing and release evidence.
