# Project Rules & Development Standards

## 1. Agent Execution & Git Submodule Workflow

To maintain clean separation and enable isolated, concurrent task execution:

When an AI agent (or human developer) picks up a task involving code changes, it **must** instantiate a Git submodule within `03_workspace/`.

### 1.1. Directory Naming Strategy

Submodule directories inside `03_workspace/` must follow the format:

$$\text{03\_workspace/}\langle\text{TASK\_ID}\rangle\_\langle\text{repo\_name}\rangle$$

**Examples:**

- `03_workspace/T-001_contracts`
- `03_workspace/T-002_relayer_backend`
- `03_workspace/T-003_mobile_app`

### 1.2. Branch Naming Strategy

Within the submodule, the agent must check out a working branch named according to the following conventions:

$$\langle\text{type}\rangle/\langle\text{TASK\_ID}\rangle\text{-}\langle\text{short-kebab-description}\rangle$$

**Prefix Types:**

- `feature/` : New features or functional additions
- `fix/` : Bug fixes and patches
- `chore/` : Tooling, dependency updates, configuration
- `refactor/` : Code refactoring without behavioral change
- `test/` : Adding or updating test suites

**Examples:**

- `feature/T-001-gasless-permit`
- `feature/T-002-relayer-tx-listener`
- `fix/T-005-pin-aes-decryption`

### 1.3. Step-by-Step Task Execution Protocol

1. **Pick Task:** Pick a task from `02_tasks/0_todo/` and move it to `02_tasks/1_in_progress/`.
2. **Sync Context:** Before anything else, re-check the shared knowledge base for
   changes since the previous task finished. At minimum, re-read `rules.md` and
   the ADRs in `01_context/adr/` to catch any new or amended rules, decisions,
   or constraints. Apply the latest guidance to the current task.
3. **Review Dependencies:** Before starting work, read the task's direct
   dependencies (its `dependencies` YAML field). For each one, review its task
   file, current status, **Agent Execution Log**, and any review notes, and take
   the resulting context, decisions, and constraints into account. Do not begin
   implementation until every direct dependency is understood (and, where
   required, completed).
4. **Create Submodule:**
    ```bash
    git submodule add <repo_url> 03_workspace/<TASK_ID>_<repo_name>
    ```
5. **Checkout Task Branch:**
    ```bash
    cd 03_workspace/<TASK_ID>_<repo_name>
    git checkout -b <type>/<TASK_ID>-<short-description>
    ```
6. **Develop & Validate:** Implement changes, run local unit/integration tests within the submodule.
7. **Commit & Push:** Commit inside the submodule following the Semantic Commit message convention with explicit reference to the linked task ID(s) (see Section 3).
8. **Task Review:** Update task metadata in `02_tasks/` and move the task file to `02_tasks/2_in_review/`.

### 1.4. Task Creation & Dependency Maintenance

Whenever a new task is created (or an existing task is split/reshaped), the
agent **must** review and update the dependency graph so it stays accurate:

1. **Declare upstream dependencies:** Populate the new task's `dependencies`
   YAML field with every task it relies on.
2. **Update downstream tasks:** Inspect existing tasks and add the new task ID
   to the `dependencies` field of any task that must not start before it. Do
   not assume the graph is static; introducing a task can retroactively block
   others.
3. **Keep the dashboard in sync:** Reflect the same dependency changes in the
   `00_DASHBOARD.md` task table so the metadata and the overview never diverge.
4. **Guard against cycles:** Verify the resulting graph remains acyclic before
   finishing.

### 1.5. Review Execution Protocol

A task sitting in `02_tasks/2_in_review/` is not complete until a reviewer (human
or agent, **other than** the implementer wherever possible) validates it and
promotes it to `3_done/`. Reviews follow this protocol:

1. **Sync Context:** As in §1.3, re-read `rules.md` and the ADRs in
   `01_context/adr/` so the review applies the latest rules and decisions.
2. **Verify Acceptance Criteria:** Walk every checkbox in the task's
   `# Acceptance Criteria` and confirm each is genuinely satisfied by evidence,
   not merely marked `[x]`.
3. **Independent Verification (do not trust the log):** Treat the Agent Execution
   Log as a claim to be re-confirmed, never as proof. Inspect the actual files
   and diff, and independently re-run the relevant validation from a clean state,
   for example:
    - Code: `npm ci` (or equivalent), build, lint, and tests; run any codegen the
      build depends on (e.g. `prisma generate`).
    - Git/infra: confirm branch/commit topology, submodule gitlink consistency
      (working checkout == recorded gitlink == remote), repository visibility, and
      access assumptions (e.g. an anonymous fetch fails when the repo is private).
4. **Security & Scope Check:** Confirm no secrets, keys, or `.env` files were
   committed (§2), and that the change stays within the task's scope. Note any
   scope creep or out-of-scope drift explicitly.
5. **Triage Findings:**
    - **Minor** (typos, doc drift, formatting, trivially safe corrections):
      fix directly as part of the review and note it in the Review Log.
    - **Medium / Major** (design concerns, missing behavior, cross-task impact,
      anything requiring a judgement call): **do not silently fix.** Notify the
      requester with options, and/or carve out a dedicated follow-up task per
      §1.4 rather than expanding the task under review.
6. **Decision:**
    - **Request changes:** set the task's `status` back to `in_progress`, move the
      file to `02_tasks/1_in_progress/`, and record the required changes in the
      Review Log. The task re-enters review once addressed.
    - **Approve:** proceed to the Approval Actions below.
7. **Approval Actions (on approve):**
    1. **Merge & Release** the task branch into the target repo's default branch
       (`main`), push it, and delete the merged branch (remote and local).
    2. **Reconcile Submodules:** update the canonical/main-tracking submodule
       gitlink to the merged commit, and remove any now-redundant per-task
       submodule from `03_workspace/` and `.gitmodules`.
    3. **Promote the Task:** set `status: done` and move the file to
       `02_tasks/3_done/`.
    4. **Keep the Dashboard in Sync:** update `00_DASHBOARD.md` (status column and
       phase narrative), consistent with §1.4.
    5. **Open Follow-ups:** create any deferred/out-of-scope tasks identified in
       triage (§1.4), so nothing is silently dropped.
8. **Record a Review Log:** append a dated `# Review Log` section to the task file
   capturing what was independently verified, the decision, the merge/release
   details (commit SHAs, branch cleanup, submodule changes), and any follow-up
   task IDs created.

> **Reviewer independence:** The value of a review comes from re-deriving the
> result, not re-reading the claim. Always reproduce validation and inspect the
> real artefacts before approving.

---

## 2. General Project Constraints

- **Language:** English is the primary language for code, documentation, commits, and task files.
- **Security:** Never commit private keys, mnemonic phrases, API secrets, or `.env` files.
- **Zero Crypto Jargon:** User-facing frontend strings and error messages must never expose low-level blockchain terms (gas, hex address, hex hash, permit bytes).

---

## 3. Commit Message Standards (Semantic Commits with Task References)

All commit messages across all repositories (main orchestrator and task submodules) must follow the **Conventional / Semantic Commits** specification and **imperatively include a contextual scope along with the linked task ID(s)** at the end of the subject line.

### 3.1. Commit Format

```text
<type>(<taskContext>): <short imperative subject> |<TASK_ID>

[optional body explaining context/rationale]

[optional footer(s)]
```

### 3.2. Allowed Commit Types

- `feat`: A new feature or functional addition
- `fix`: A bug fix or patch
- `chore`: Tooling, configuration, dependency updates, or repository maintenance
- `refactor`: Code refactoring with no behavioral change
- `test`: Adding or updating test suites
- `docs`: Documentation updates or context additions
- `ci`: Continuous Integration / Continuous Deployment pipeline changes
- `perf`: Performance improvements

### 3.3. Commit Rules

1. **Task Context Scope:** The parentheses immediately following the type specify the task/feature context (e.g., `backendSetup`, `deployConfig`, `auth`, `permitQueue`).
2. **Task ID Reference:** Every commit must end the subject line with a pipe delimiter followed by the associated task ID, e.g., `|T-001`. For commits touching multiple tasks, list all linked IDs separated by commas (e.g., `|T-001,T-002`).
3. **Imperative Mood:** The subject line must use the imperative mood (e.g., "add", "implement", "fix", not "added", "implements", "fixing").
4. **Concise Subject:** Keep the subject line clear and concise, lowercase/standard casing, and do not end with a period.
5. **Separation:** If a body is provided, separate it from the subject line with a blank line and wrap at 72 characters.

### 3.4. Examples

- `feat(backendSetup): scaffold nestjs relayer with docker and docker-compose |T-001`
- `chore(deployConfig): configure redis and postgres healthchecks in compose file |T-001`
- `feat(database): implement prisma schema for users and cloud backups |T-002`
- `fix(pinCrypto): resolve aes-256 decryption padding on mobile backup recovery |T-005`
- `test(permitExecution): add unit tests for eip-2612 permit simulation |T-003`
- `docs(adr): document relayer architecture and containerization stack |T-001`
