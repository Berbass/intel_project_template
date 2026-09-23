# Agent Instructions — `<CHILD_REPO_NAME>`

> **Template usage:** This file is a reusable contract. Drop it into a derived
> (child) code repository as its own `AGENTS.md` and replace every `<PLACEHOLDER>`
> with concrete values. Keep it lean — it points to canonical references, it does
> not copy them.

This repository is a **child** of an AI-agent orchestrator. The orchestrator
decides *why* and *what next*; this repo owns *how it runs, builds, and tests*.
An agent working here receives its task and context from the orchestrator, then
executes the implementation detail locally.

## Canonical References (source of truth — read, don't duplicate)

Do not restate the content below; follow the linked source so it stays current.

- **This repo's README:** `<path/to/README.md>` — purpose, architecture, entry points.
- **Contributing guide:** `<path/to/CONTRIBUTING.md>` — local setup, PR flow, coding standards.
- **Developer docs:** `<path/to/docs/>` — deeper design, runtime, and integration notes.
- **Build / test scripts:** `<build command>`, `<test command>`, `<lint command>` (see `<package manifest / Makefile>`).
- **Orchestrator repo:** `<ORCHESTRATOR_REPO_URL>` — backlog, task state, ADRs, and
  the project rules (`01_context/rules.md`). Orchestrator rules govern; this
  contract references them rather than repeating them.

## Non-Negotiable Operational Invariants

An agent working in this repo must **always** honor these, without exception:

- **No secrets:** Never commit private keys, credentials, API secrets, tokens, or
  `.env` files. Use the repo's ignored/local config mechanism.
- **English everywhere:** Code, comments, commit messages, and docs are in English.
- **Commit format:** Follow Conventional / Semantic Commits and end the subject
  line with the linked task ID: `<type>(<scope>): <imperative subject> |T-XXX`.
  For multiple tasks, list IDs comma-separated (e.g. `|T-XXX,T-YYY`).
- **Stay in scope:** Implement only what the linked task asks. Surface scope creep
  back to the orchestrator as a follow-up task instead of silently expanding work.
- **Validate before handing back:** Run this repo's own validation
  (`<build command>`, `<test command>`, `<lint command>`) and confirm it passes
  cleanly before moving the task to review.
- **Backward compatibility:** Keep changes backward-compatible for downstream
  consumers, or ship an explicit migration note alongside the change.

## Orchestrator vs. Child — Source-of-Truth Boundary

Respect the split. Each side owns distinct decisions; do not migrate one side's
responsibilities into the other.

| Concern | Owner | Lives in |
| --- | --- | --- |
| Backlog, task state, priorities | **Orchestrator** | `<ORCHESTRATOR_REPO_URL>` `02_tasks/` |
| Cross-repo decisions, ADRs, "why" | **Orchestrator** | `<ORCHESTRATOR_REPO_URL>` `01_context/adr/` |
| Review gate & promotion to done | **Orchestrator** | `<ORCHESTRATOR_REPO_URL>` `rules.md` |
| Local dev & environment setup | **Child** | this repo (`README`, `CONTRIBUTING`) |
| Build, test, lint, runtime specifics | **Child** | this repo (`<build/test/lint scripts>`) |
| Implementation & code structure | **Child** | this repo source tree |

**In short:**

- The **orchestrator** answers *why this work exists* and *what comes next* —
  backlog, task lifecycle, cross-repo decisions, ADRs, and the review gate.
- This **child repo** answers *how to run it*, *how to test it*, and *how it's
  built* — local dev, build, test, and runtime specifics.
- An agent **pulls task and context from the orchestrator** and **executes the
  implementation detail here**, then returns the task to the orchestrator's
  review gate.
