# Context CHANGELOG

A running, human- and agent-readable log of **notable changes to the shared
knowledge base** — anything under `01_context/` (rules, ADRs, glossary,
documentation, templates) plus cross-cutting workflow conventions. It exists so a
new session can answer "what changed since I last synced?" in one glance without
diffing the whole repo.

This file complements, but does not replace, Git history and the ADRs:

- **Git history** is the exhaustive, low-level record of every commit.
- **ADRs** (`01_context/adr/`) hold the _rationale_ for architectural decisions
  and are immutable once accepted (superseded, never edited — see
  `project_structure_guidelines.md`).
- **This CHANGELOG** is the curated, chronological digest of context changes that
  agents and humans should notice at session start.

## Entry Convention

Add one line per notable change, newest first, under the current date. Keep it to
a single imperative sentence and reference the driving task ID(s):

```text
- YYYY-MM-DD — <one-line imperative summary of the context change> (T-XXX)
```

Rules:

- **One line per change.** If a change needs a paragraph, it probably needs an ADR
  or a dedicated doc; link to that instead.
- **Newest first**, grouped under a `## YYYY-MM-DD` date heading.
- **Reference the task.** End each entry with the linked task ID(s) in
  parentheses, e.g. `(T-009)` or `(T-011, T-012)`.
- **Context only.** Log changes to the shared knowledge base and workflow
  conventions — not routine target-repo feature work, which lives in task files
  and Git history.

## Log

## 2026-09-24

- Establish the context CHANGELOG and formalize the source-of-truth model: task
  files are authoritative for task state, the dashboard is a derived view, and
  implementer- vs. reviewer-owned fields are documented in `rules.md` §1.6 (T-009)
