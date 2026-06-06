# AI-Driven Project Structure Guidelines

## Overview

This document outlines the standard file and directory structure used across this project.
The primary goal of this architecture is to provide a reliable, stateful, and easily parsable environment for Autonomous AI Agents. Since Large Language Models (LLMs) lack persistent memory across sessions, this file structure acts as their **shared memory, state management system, and Kanban board**.

By strictly adhering to this structure and the use of Markdown with YAML Frontmatter, we ensure that AI agents can effectively read context, track progress, manage dependencies, and collaborate without losing sight of the project's goals.

## Directory Structure

```text
📁 project-root/
├── 📁 01_context/               # The "Knowledge Base" (Read-Only for task agents)
│   ├── rules.md                 # General project constraints and coding/writing standards
│   ├── glossary.md              # Domain-specific terminology
│   └── 📁 adr/                  # Architecture Decision Records (Historical choices)
├── 📁 02_tasks/                 # The Backlog & Workflow (State Management)
│   ├── 📁 0_todo/               # Tasks ready to be picked up
│   ├── 📁 1_in_progress/        # Tasks currently being worked on by an agent or human
│   ├── 📁 2_in_review/          # Tasks awaiting QA or peer review
│   └── 📁 3_done/               # Completed and validated tasks
├── 📁 03_workspace/             # The "Scratchpad"
│   └── draft_feature.md         # Temporary area for agents to iterate, brainstorm, or generate code
├── 📁 01_context/documentation/         # Project meta-documentation
│   └── project_structure_guidelines.md (This file)
├── 📁 04_deliverables/          # The final output
│   └── (compiled code, final docs, etc.)
├── 00_DASHBOARD.md              # Executive summary updated automatically/manually
└── README.md                    # Main entry point with links
```

## Detailed Usage Guidelines

### 1. `01_context/` (The Brain)

This directory acts as the foundational knowledge for any AI agent joining the project.

* **Usage:** Before starting any task, agents are instructed to read relevant files here to align with project rules, tone, and historical decisions.

* **The `adr/` subfolder:** Contains *Architecture Decision Records*. Every major choice (e.g., "Why we chose React over Vue") is documented here as a numbered file (e.g., `001-frontend-framework.md`). This prevents agents from revisiting settled debates or making inconsistent suggestions.

### 2. `02_tasks/` (The Engine)

This is where the actual project management happens. We move `.md` files between subdirectories to represent state changes.

#### The YAML Frontmatter Rule

**Every** file inside the `02_tasks/` directory **MUST** begin with a YAML Frontmatter block. This is critical for AI agents to quickly parse metadata without reading the entire document.

**Template for a Task File (`task_xxx.md`):**

\`\`\`yaml
---
id: T-015
title: "Implement User Authentication"
status: in_progress
assigned_to: agent_backend
dependencies: [T-010, T-012]
completion_percentage: 50%
last_updated: 2026-05-27
---
\`\`\`

# Objective
Briefly describe what needs to be achieved.

# Acceptance Criteria
- [x] Criterion 1 completed
- [ ] Criterion 2 pending

# Agent Execution Log
*Optional: Agents can append notes here regarding their thought process, blockers, or why they paused execution.*


#### Workflow Execution

1. An agent picks a file from `0_todo/`.

2. The agent updates the YAML `status` to `in_progress` and **physically moves** the file to the `1_in_progress/` directory.

3. The agent executes the work (often drafting in the `03_workspace/`).

4. Once the Acceptance Criteria are met, the agent updates the `status` to `in_review` and moves the file to `2_in_review/`.

5. A QA agent (or human) reviews the work. If approved, it moves to `3_done/`.

### 3. `03_workspace/` (The Scratchpad)

Agents generate intermediate thoughts, partial code snippets, or rough drafts here.

* **Usage:** This prevents cluttering the final deliverables or the task descriptions. Files here are considered ephemeral and can be overwritten or deleted once the task is marked as `done`.

### 4. `00_DASHBOARD.md` (The Overview)

A high-level summary of the project state.

* **Usage:** Can be maintained by a "Project Manager" AI agent. It parses the `02_tasks/` directory periodically to aggregate metrics (e.g., "5 tasks in progress, 2 blocked") for human oversight.
