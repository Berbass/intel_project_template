# 📊 Project Dashboard

> **Derived view — not the source of truth.** This dashboard is a human-friendly
> summary _aggregated from_ the task files in `02_tasks/`. The task files are the
> single source of truth for task state (see `rules.md` §1.6). When this page and
> a task file disagree, **the task file wins** — update this page to match.

## Project Overview

_One or two paragraphs: what this project is, its goal, and the current headline
status. Keep it current but brief — details live in the task files and
`01_context/`._

## Current Focus

_The active phase and what's in flight right now. Narrative, not authoritative._

- In progress: _…_
- In review: _…_
- Next up / blocked: _…_

## Roadmap / Phases

- **Phase 0 — …:** _short description._
- **Phase 1 — …:** _short description._

## Task Registry

_A convenience snapshot mirrored from `02_tasks/`. If a row here disagrees with a
task file, the task file is correct._

| Task ID | Title | Status | Assignee | Dependencies | Target Repo |
| ------- | ----- | ------ | -------- | ------------ | ----------- |
| T-001   | _…_   | `todo` | _…_      | None         | _…_         |

_Keep the dependency graph acyclic (`rules.md` §1.4). To check registry/task-file
parity automatically, run `python3 scripts/lint_backlog.py`._
