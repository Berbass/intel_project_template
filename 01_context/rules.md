# Project Rules & Development Standards

## 1. Agent Execution & Git Worktree Workflow

To maintain clean separation and enable isolated, concurrent task execution, the
workspace for code changes lives under `03_workspace/`.

**Default: Git worktrees.** The common case is a single target repository worked
on across many concurrent task branches. For this case an agent (or human
developer) picking up a task involving code changes **must** create a Git
_worktree_ per task inside `03_workspace/`. A worktree gives each task an
isolated working directory and its own branch while sharing one local object
store — far less metadata churn than submodules (see ADR-001, §Decision.3).

**Exception: Git submodules for genuine multi-repo tasks.** Reach for a submodule
_only_ when a task must coordinate changes across _distinct_ repositories that
need to be vendored/pinned inside the orchestrator. Do not use submodules for the
ordinary single-repo, many-branches case.

Always pair setup with mirrored teardown (§1.3) so `03_workspace/` never
accumulates stale checkouts.

### 1.1. Directory Naming Strategy

Worktree (and, in the multi-repo exception, submodule) directories inside
`03_workspace/` must follow the format:

$$\text{03\_workspace/}\langle\text{TASK\_ID}\rangle\_\langle\text{repo\_name}\rangle$$

**Examples:**

- `03_workspace/T-001_contracts`
- `03_workspace/T-002_relayer_backend`
- `03_workspace/T-003_mobile_app`

### 1.2. Branch Naming Strategy

Within the worktree (or, in the multi-repo exception, the submodule), the agent must check out a working branch named according to the following conventions:

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
   changes since the previous task finished. Skim `01_context/CHANGELOG.md` for a
   quick digest of what changed, then re-read `rules.md` and the ADRs in
   `01_context/adr/` to catch any new or amended rules, decisions, or
   constraints. Apply the latest guidance to the current task.
3. **Review Dependencies:** Before starting work, read the task's direct
   dependencies (its `dependencies` YAML field). For each one, review its task
   file, current status, **Agent Execution Log**, and any review notes, and take
   the resulting context, decisions, and constraints into account. Do not begin
   implementation until every direct dependency is understood (and, where
   required, completed).
4. **Create Worktree (default):** From a local clone of the target repository,
   create the isolated worktree and its task branch in a single step:
    ```bash
    git worktree add -b <type>/<TASK_ID>-<short-description> \
      <orchestrator_root>/03_workspace/<TASK_ID>_<repo_name> main
    ```
    _Multi-repo exception only:_ if the task genuinely spans distinct
    repositories, add a submodule instead and branch inside it:
    ```bash
    git submodule add <repo_url> 03_workspace/<TASK_ID>_<repo_name>
    cd 03_workspace/<TASK_ID>_<repo_name>
    git checkout -b <type>/<TASK_ID>-<short-description>
    ```
5. **Develop & Validate:** Implement changes and run local unit/integration tests
   within the worktree.
6. **Commit & Push:** Commit inside the worktree following the Semantic Commit
   message convention with explicit reference to the linked task ID(s) (see
   Section 3).
7. **Task Review:** Update task metadata in `02_tasks/` and move the task file to
   `02_tasks/2_in_review/`.
8. **Teardown (mandatory on completion):** A task's workspace **must not** outlive
   its promotion to `3_done/`. As soon as the task is merged and promoted, remove
   its worktree and delete the task branch so `03_workspace/` never accumulates
   stale checkouts. Setup and teardown must mirror each other:

    ```bash
    # From the target repository clone:
    git worktree remove 03_workspace/<TASK_ID>_<repo_name>
    git branch -d <type>/<TASK_ID>-<short-description>
    git worktree prune
    git push origin --delete <type>/<TASK_ID>-<short-description>  # drop merged remote branch
    ```

    _Multi-repo exception:_ deinitialize and remove the submodule instead
    (`git submodule deinit <path>`, `git rm 03_workspace/<TASK_ID>_<repo_name>`,
    and drop its `.gitmodules` entry).

    To audit or enforce this mandate in bulk, run the zero-dependency helper
    `python3 scripts/prune_workspace.py` (dry-run) or `--apply` to remove the
    worktrees of every task already in `3_done/`.

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

**Review-queue ordering (topological).** When multiple tasks await review, process
them in dependency order — a task's upstream dependencies must be reviewed and
merged before the task itself. Never promote a task ahead of an unreviewed
dependency, because its diff and validation assume the upstream change is already
on `main`.

1. **Sync Context:** As in §1.3, re-read `rules.md` and the ADRs in
   `01_context/adr/` so the review applies the latest rules and decisions.
2. **Verify Acceptance Criteria:** Walk every checkbox in the task's
   `# Acceptance Criteria` and confirm each is genuinely satisfied by evidence,
   not merely marked `[x]`.
3. **Independent Verification (do not trust the log):** Treat the Agent Execution
   Log as a claim to be re-confirmed, never as proof. Inspect the actual files
   and diff, and independently re-run the relevant validation from a clean state,
   for example:
    - Code: run the repo's validation from a clean state — `npm ci` (or
      equivalent), build, lint, tests, and any codegen the build depends on (e.g.
      `prisma generate`). Validation must be **zero-warning**, not merely
      zero-error. Run it through the project's shared tooling / runtime seam (the
      agreed interpreter, virtualenv, or task runner) rather than an ad-hoc local
      environment, so results are reproducible across reviewers.
    - Git/infra: confirm branch/commit topology and that the task branch is based
      on current `main`. For worktree tasks, verify the worktree is clean and its
      branch pushed; for the multi-repo exception, verify submodule gitlink
      consistency (working checkout == recorded gitlink == remote). Confirm
      repository visibility and access assumptions (e.g. an anonymous fetch fails
      when the repo is private).
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
7. **Approval Actions (on approve).** Releases happen in two tiers — first the
   **target repo(s)**, then the **orchestrator repo** — and a task is not promoted
   until both are reconciled:

    **Tier 1 — Target-repo release:**
    1. **Merge & Release** the task branch into the target repo's default branch
       (`main`), push it, and delete the merged branch (remote and local). For a
       cross-repo task, repeat this for every target repo it touches.
    2. **Tear down the workspace:** remove the task worktree and prune per §1.3
       step 8 (mandatory; `scripts/prune_workspace.py` can audit/enforce it).
       _Multi-repo exception:_ instead update the canonical submodule gitlink to
       the merged commit and remove the per-task submodule from `03_workspace/`
       and `.gitmodules`.

    **Tier 2 — Orchestrator reconciliation:**

    3. **Context & Spec Reconciliation gate (before promotion):** confirm the
       orchestrator knowledge base is internally consistent with the merged
       change — a `grep` across `01_context/` for the deprecated/superseded terms
       the task was meant to remove returns **zero** results, cross-references
       still resolve, and any ADR the change invalidates has been _superseded_
       (not edited in place) per the guidelines. Do not promote while this gate is
       red.
    4. **Promote the Task:** set `status: done` and `review_status: approved`,
       fill `reviewed_by` / `reviewed_at`, and move the file to
       `02_tasks/3_done/`.
    5. **Keep the Dashboard in Sync:** update `00_DASHBOARD.md` (status column and
       phase narrative), consistent with §1.4.
    6. **Open Follow-ups:** create any deferred/out-of-scope tasks identified in
       triage (§1.4), so nothing is silently dropped.

8. **Record a Review Log:** append a dated `# Review Log` section to the task file
   capturing what was independently verified, the decision, the merge/release
   details (commit SHAs, branch cleanup, worktree teardown — submodule changes
   only in the multi-repo exception), and any follow-up task IDs created.

> **Reviewer independence:** The value of a review comes from re-deriving the
> result, not re-reading the claim. Always reproduce validation and inspect the
> real artefacts before approving.

### 1.6. Source of Truth & Field Ownership

Task state is tracked in two places — the per-task files under `02_tasks/**` and
the registry in `00_DASHBOARD.md`. To keep them from drifting, exactly one is
authoritative:

- **Task files are the single source of truth.** A task's canonical state — its
  lifecycle `status`, metadata (frontmatter), execution log, and review log —
  lives in its `.md` file under `02_tasks/`. The file's **directory** (`0_todo/`,
  `1_in_progress/`, `2_in_review/`, `3_done/`) and its `status` field are the
  authoritative signal of where the task is.
- **The dashboard is a derived, narrative view.** `00_DASHBOARD.md` summarizes and
  narrates the backlog for humans; it is _aggregated from_ the task files and is
  never authoritative. **When the dashboard and a task file disagree, the task
  file wins** — fix the dashboard to match, not the other way around.
- **Context changes are logged.** Notable changes to the shared knowledge base
  (`01_context/`) are recorded in `01_context/CHANGELOG.md` per its entry
  convention, so a new session can catch up without diffing history.

**Field ownership.** Each frontmatter field has one owner; only its owner may
change it, which keeps implementer and reviewer responsibilities from colliding
(see the review protocol, §1.5):

- **Implementer-owned** (set/updated while doing the work): `status` transitions
  through `todo → in_progress → in_review`, `assigned_to`, `completion_percentage`,
  `branch`, `base_commit`, `worktree`, `validation`, `last_updated`, and the
  `# Agent Execution Log`.
- **Reviewer-owned** (set only during review, §1.5): `review_status`,
  `reviewed_by`, `reviewed_at`, the final `status: done` promotion (and the move
  to `3_done/`), and the `# Review Log`.

The implementer moves a task as far as `2_in_review/`; only a reviewer performs
the final promotion to `done`. An implementer must not self-set the review fields
or promote their own task, and a reviewer must not rewrite the execution log or
metadata to mask a problem — request changes instead (§1.5 step 6).

---

## 2. General Project Constraints

- **Language:** English is the primary language for code, documentation, commits, and task files.
- **Security:** Never commit private keys, mnemonic phrases, API secrets, or `.env` files.
- **Zero Crypto Jargon:** User-facing frontend strings and error messages must never expose low-level blockchain terms (gas, hex address, hex hash, permit bytes).

---

## 3. Commit Message Standards (Semantic Commits with Task References)

All commit messages across all repositories (the orchestrator repo and its task worktrees; submodules only in the multi-repo exception) must follow the **Conventional / Semantic Commits** specification and **imperatively include a contextual scope along with the linked task ID(s)** at the end of the subject line.

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

### 3.5. Orchestrator & Cross-Repo Commit Convention

Commits fall into two tiers that mirror the two-tier release in §1.5:

1. **Target-repo commits** (the deliverable): follow §3.1–§3.4 inside the task
   worktree of the target repository.
2. **Orchestrator-repo commits** (task management — task files, `00_DASHBOARD.md`,
   `01_context/` changes made directly in the orchestrator): also use Semantic
   Commits with a management-oriented scope such as `backlog`, `review`,
   `dashboard`, or `orchestration`, and the same trailing `|T-XXX` reference.
   Example: `chore(review): promote T-007 to done and sync dashboard |T-007`.

**Cross-repo tasks.** When a single task changes more than one target repo:

- Each repository receives its own commit(s), and every such commit ends with the
  same task ID reference (list all linked IDs when several tasks share the work,
  e.g. `|T-011,T-012`).
- Keep each repo's commit scoped to that repo's change; do not bundle unrelated
  repos behind one message.
- Record the cross-repo release set (repos, branches, and merged commit SHAs) in
  the task's `# Review Log` so the distributed change is auditable from one place.
