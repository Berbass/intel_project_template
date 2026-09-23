# AI-Driven Project Structure Guidelines

## Overview

This document outlines the standard file and directory structure used across this project.
The primary goal of this architecture is to provide a reliable, stateful, and easily parsable environment for Autonomous AI Agents. Since Large Language Models (LLMs) lack persistent memory across sessions, this file structure acts as their **shared memory, state management system, and Kanban board**.

By strictly adhering to this structure and the use of Markdown with YAML Frontmatter, we ensure that AI agents can effectively read context, track progress, manage dependencies, and collaborate without losing sight of the project's goals.

## Directory Structure

```text
📁 project-root/
├── 📁 01_context/                 # The "Knowledge Base" (Read-Only for task agents)
│   ├── rules.md                   # Project rules & git worktree/submodule protocol
│   ├── glossary.md                # Domain-specific and technical terminology
│   ├── 📁 adr/                    # Architecture Decision Records (Historical choices)
│   └── 📁 documentation/          # Project specifications and guidelines
│       ├── global_specifications.md
│       └── project_structure_guidelines.md
├── 📁 02_tasks/                   # The Backlog & Workflow (State Management)
│   ├── 📁 0_todo/                 # Tasks ready to be picked up
│   ├── 📁 1_in_progress/          # Tasks currently being worked on
│   ├── 📁 2_in_review/            # Tasks awaiting QA or peer review
│   └── 📁 3_done/                 # Completed and validated tasks
├── 📁 03_workspace/               # The "Scratchpad" & Task Worktrees
│   └── 📁 T-015_repo_name/        # Isolated Git worktree for active task
├── 00_DASHBOARD.md                # Executive summary of project state
└── README.md                      # Main entry point with links
```

## Detailed Usage Guidelines

### 1. `01_context/` (The Brain)

This directory acts as the foundational knowledge for any AI agent joining the project.

- **Usage:** Before starting any task, agents are instructed to read relevant files here (`rules.md`, `project_structure_guidelines.md`, `glossary.md`, `global_specifications.md`) to align with project rules, tone, and historical decisions.
- **The `adr/` subfolder:** Contains _Architecture Decision Records_. Every major choice (e.g., "Why we chose Flutter over React Native") is documented here as a numbered file (e.g., `001-frontend-framework.md`). This prevents agents from revisiting settled debates.

    **ADR governance (immutability + supersede).** Accepted ADRs are immutable: never edit the Decision of an accepted ADR in place. When a new decision invalidates an accepted one, write a _new_ numbered ADR that links back to the one it replaces, and set the old ADR's Status to `Superseded by ADR-00X` while leaving its body intact as the historical record. **Trigger:** any change that invalidates an accepted ADR — a reversal, a material scope shift, or a technology/workflow pivot — requires a new ADR _before_ the change lands. For pivots, start from the template at `01_context/adr/template_pivot_adr.md`.

### 2. `02_tasks/` (The Engine)

This is where the actual project management happens. We move `.md` files between subdirectories to represent state changes.

#### The YAML Frontmatter Rule

**Every** file inside the `02_tasks/` directory **MUST** begin with a YAML Frontmatter block.

**Template for a Task File (`task_xxx.md`):**

```yaml
---
id: T-015
title: "Implement Gasless Permit Execution in Relayer"
status: in_progress          # todo | in_progress | in_review | done
assigned_to: agent_backend
dependencies: [T-010]
# Single-repo (common case) — a string:
target_repo: "https://github.com/organization/repo_name"
# Multi-repo (cross-repo tasks) — use a list *instead of* target_repo:
# target_repos:
#   - "https://github.com/organization/repo_contracts"
#   - "https://github.com/organization/repo_backend"
completion_percentage: 50%
# --- Execution (worktree) metadata — implementer-owned; filled in when work starts ---
branch: "feature/T-015-gasless-permit"
base_commit: "<sha the worktree was branched from>"
worktree: "03_workspace/T-015_repo_name"
validation: pending          # pending | passing | failing
# --- Review metadata — reviewer-owned; filled in during review (see rules.md §1.5) ---
review_status: pending       # pending | approved | changes_requested
reviewed_by: ""
reviewed_at: ""
last_updated: 2026-08-19
---

# Objective

Briefly describe what needs to be achieved.

# Acceptance Criteria

- [x] Criterion 1 completed
- [ ] Criterion 2 pending

# Definition of Done

> DoD reminder: every Acceptance Criterion satisfied, changes validated (worktree
> tests/lint green, zero stale references, no secrets), and approved via
> independent review per `rules.md` §1.5.

# Agent Execution Log

_Notes regarding thought process, blockers, or execution details._

# Review Log

_Reviewer-owned (`rules.md` §1.5). Dated entries recording what was independently
verified, the decision, merge/release details (commit SHAs, branch cleanup), and
any follow-up task IDs created._

# Follow-ups / Deferred

_Out-of-scope or deferred items surfaced during execution or review. Each should
become its own task (`rules.md` §1.4); list the created task IDs here so nothing
is silently dropped._
```

**Field notes & backward compatibility:**

- **Additive & optional.** The execution and review fields (`branch`,
  `base_commit`, `worktree`, `validation`, `review_status`, `reviewed_by`,
  `reviewed_at`) are populated as a task progresses. Existing task files that
  predate these fields remain valid — add the fields when a task next moves
  state; no bulk migration is required.
- **`target_repo` vs `target_repos`.** Keep the single `target_repo` string for
  the common single-repo case. Use the `target_repos` list _only_ for genuine
  cross-repo tasks; do not set both.
- **Ownership.** Implementer-owned vs. reviewer-owned fields are grouped by the
  inline comments above (formal ownership rules live in `rules.md`).

#### Workflow Execution

1. An agent picks a file from `0_todo/`.
2. The agent updates the YAML `status` to `in_progress` and **physically moves** the file to `1_in_progress/`.
3. If code changes are required, the agent instantiates a Git worktree in `03_workspace/` (see section 3 below); submodules are used only for the genuine multi-repo case.
4. Once the Acceptance Criteria are met and tests pass, the agent updates `status` to `in_review` and moves the file to `2_in_review/`.
5. A reviewer validates the work. If approved, it moves to `3_done/`.

### 3. `03_workspace/` (The Scratchpad & Task Worktrees)

Agents use this directory for drafting intermediate work, code experiments, and isolated per-task working directories.

- **Git Worktree Strategy (default):** For a task changing a single target repository on its own branch, the agent creates a Git _worktree_ inside `03_workspace/`. Each task gets an isolated working directory and branch backed by one shared object store (see ADR-001 and `rules.md` §1). Submodules are reserved for the genuine multi-repo case.
- **Directory Naming Strategy:**
  `03_workspace/<TASK_ID>_<repo_name>` (e.g., `03_workspace/T-015_repo_name`).
- **Branch Naming Strategy:**
  `<type>/<TASK_ID>-<short-description>` (e.g., `feature/T-015-gasless-permit`, `fix/T-016-pin-crypto`).
- **Setup / Teardown:** Always pair `git worktree add` with a mirrored `git worktree remove` + branch deletion once the task reaches `3_done/`, so the scratchpad never accumulates stale checkouts. See `rules.md` §1.3 for the exact commands.

### 4. `00_DASHBOARD.md` (The Overview)

A high-level summary of the project state aggregated from `02_tasks/`.
