#!/usr/bin/env python3
"""Validate the integrity of the ``02_tasks/`` backlog and its dashboard.

Zero-dependency (stock Python 3, no third-party packages). The linter checks:

1. **Frontmatter shape** \u2014 every task file carries a well-formed YAML frontmatter
   block with the required keys.
2. **Status/directory parity** \u2014 each task's ``status`` matches the Kanban folder
   it lives in (``0_todo`` -> ``todo``, ... ``3_done`` -> ``done``).
3. **Dependencies** \u2014 every declared dependency refers to an existing task, and
   the dependency graph is acyclic (a DAG).
4. **Dashboard sync** \u2014 the ``00_DASHBOARD.md`` task registry lists exactly the
   existing tasks, with matching status.

On any violation it prints a readable, grouped error list and exits non-zero.

Usage::

    python3 scripts/lint_backlog.py                 # lint the current project
    python3 scripts/lint_backlog.py --root /path     # lint an explicit root
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

STATUS_BY_DIR = {
    "0_todo": "todo",
    "1_in_progress": "in_progress",
    "2_in_review": "in_review",
    "3_done": "done",
}
VALID_STATUSES = set(STATUS_BY_DIR.values())

# Core keys every task frontmatter must carry. Execution/review fields
# (branch, base_commit, worktree, validation, review_status, ...) are optional
# and adopted as a task progresses, so they are intentionally not required here.
REQUIRED_KEYS = [
    "id",
    "title",
    "status",
    "assigned_to",
    "dependencies",
    "completion_percentage",
    "last_updated",
]
TASK_ID_RE = re.compile(r"^T-\d+$")


def find_project_root(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / "02_tasks").is_dir():
            return candidate
    return None


def split_frontmatter(text: str) -> dict[str, str] | None:
    """Return the raw ``key -> value`` map of the leading YAML frontmatter.

    Returns ``None`` if no ``--- ... ---`` block starts the file. Values are
    kept as raw strings (list values keep their surrounding brackets); block
    lists are folded into the preceding key.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fields: dict[str, str] = {}
    last_key: str | None = None
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        if not line.strip():
            continue
        block_item = re.match(r"^\s+-\s+(.*)$", line)
        if block_item and last_key is not None:
            fields[last_key] = (
                fields.get(last_key, "") + "," + block_item.group(1)
            ).strip(",")
            continue
        kv = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if kv:
            last_key = kv.group(1)
            fields[last_key] = kv.group(2).strip()
    return None  # no closing '---'


def parse_list(raw: str) -> list[str]:
    """Parse ``[A, B]`` / ``[]`` / folded block lists into a list of tokens."""
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]
    return [tok.strip().strip("\"'") for tok in raw.split(",") if tok.strip()]


def load_tasks(tasks_dir: Path, errors: list[str]) -> dict[str, dict]:
    """Load and shape-check every task file. Returns ``id -> task info``."""
    tasks: dict[str, dict] = {}
    for sub, expected_status in STATUS_BY_DIR.items():
        d = tasks_dir / sub
        if not d.is_dir():
            continue
        for md in sorted(d.glob("*.md")):
            rel = md.relative_to(tasks_dir.parent)
            fields = split_frontmatter(md.read_text(encoding="utf-8", errors="replace"))
            if fields is None:
                errors.append(f"{rel}: missing or unterminated YAML frontmatter block")
                continue
            missing = [k for k in REQUIRED_KEYS if k not in fields]
            if missing:
                errors.append(
                    f"{rel}: frontmatter missing key(s): {', '.join(missing)}"
                )
            if "target_repo" not in fields and "target_repos" not in fields:
                errors.append(
                    f"{rel}: frontmatter must set 'target_repo' or 'target_repos'"
                )

            tid = fields.get("id", "").strip().strip("\"'")
            if not TASK_ID_RE.match(tid):
                errors.append(
                    f"{rel}: invalid or missing task id '{tid}' (expected T-<n>)"
                )
                continue

            status = fields.get("status", "").strip().strip("\"'")
            if status not in VALID_STATUSES:
                errors.append(f"{rel}: invalid status '{status}'")
            elif status != expected_status:
                errors.append(
                    f"{rel}: status '{status}' does not match directory '{sub}' "
                    f"(expected '{expected_status}')"
                )

            if tid in tasks:
                errors.append(
                    f"{rel}: duplicate task id '{tid}' (also {tasks[tid]['rel']})"
                )
                continue

            tasks[tid] = {
                "rel": str(rel),
                "status": status,
                "deps": parse_list(fields.get("dependencies", "[]")),
            }
    return tasks


def check_dependencies(tasks: dict[str, dict], errors: list[str]) -> None:
    for tid, info in sorted(tasks.items()):
        for dep in info["deps"]:
            if dep not in tasks:
                errors.append(f"{info['rel']}: dependency '{dep}' does not exist")


def check_acyclic(tasks: dict[str, dict], errors: list[str]) -> None:
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {tid: WHITE for tid in tasks}

    def visit(node: str, stack: list[str]) -> bool:
        color[node] = GRAY
        for dep in tasks[node]["deps"]:
            if dep not in tasks:
                continue
            if color[dep] == GRAY:
                cycle = " -> ".join(stack[stack.index(dep) :] + [dep])
                errors.append(f"dependency cycle detected: {cycle}")
                return True
            if color[dep] == WHITE and visit(dep, stack + [dep]):
                return True
        color[node] = BLACK
        return False

    for tid in sorted(tasks):
        if color[tid] == WHITE and visit(tid, [tid]):
            return


def parse_dashboard(dashboard: Path, errors: list[str]) -> dict[str, str] | None:
    """Return ``id -> status`` from the dashboard registry table, or ``None``."""
    if not dashboard.is_file():
        errors.append(f"{dashboard.name}: not found (cannot verify registry sync)")
        return None
    header_cells: list[str] | None = None
    id_col = status_col = None
    registry: dict[str, str] = {}
    for line in dashboard.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header_cells is None:
            lowered = [c.lower() for c in cells]
            if "task id" in lowered and "status" in lowered:
                header_cells = cells
                id_col = lowered.index("task id")
                status_col = lowered.index("status")
            continue
        if set("".join(cells)) <= set("-: "):  # markdown separator row
            continue
        if (
            id_col is None
            or status_col is None
            or len(cells) <= max(id_col, status_col)
        ):
            continue
        tid = cells[id_col].strip().strip("`")
        if not TASK_ID_RE.match(tid):
            continue
        registry[tid] = cells[status_col].strip().strip("`").lower()
    if header_cells is None:
        errors.append(
            f"{dashboard.name}: no task registry table found (headers 'Task ID' + 'Status')"
        )
        return None
    return registry


def check_dashboard_sync(
    tasks: dict[str, dict], registry: dict[str, str] | None, errors: list[str]
) -> None:
    if registry is None:
        return
    for tid, info in sorted(tasks.items()):
        if tid not in registry:
            errors.append(
                f"00_DASHBOARD.md: task {tid} missing from the registry table"
            )
        elif registry[tid] != info["status"]:
            errors.append(
                f"00_DASHBOARD.md: {tid} status '{registry[tid]}' != task file "
                f"'{info['status']}'"
            )
    for tid in sorted(registry):
        if tid not in tasks:
            errors.append(
                f"00_DASHBOARD.md: registry lists {tid} with no matching task file"
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lint the 02_tasks/ backlog integrity."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Project root (auto-detected if omitted).",
    )
    args = parser.parse_args(argv)

    root = (
        args.root
        or find_project_root(Path.cwd())
        or find_project_root(Path(__file__).resolve().parent)
    )
    if root is None:
        print(
            "error: could not locate a project root containing 02_tasks/ (use --root)",
            file=sys.stderr,
        )
        return 2
    root = root.resolve()

    errors: list[str] = []
    tasks = load_tasks(root / "02_tasks", errors)
    check_dependencies(tasks, errors)
    check_acyclic(tasks, errors)
    registry = parse_dashboard(root / "00_DASHBOARD.md", errors)
    check_dashboard_sync(tasks, registry, errors)

    if errors:
        print(f"backlog lint FAILED \u2014 {len(errors)} issue(s):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"backlog lint OK \u2014 {len(tasks)} task(s) validated, dashboard in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
