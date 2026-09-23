#!/usr/bin/env python3
"""Prune 03_workspace/ entries that belong to completed (3_done) tasks.

This is a zero-dependency helper (stock Python 3, no third-party packages). It
compares the task IDs found in ``02_tasks/3_done/`` against the per-task
workspaces in ``03_workspace/`` and removes the workspaces whose task is done,
keeping the scratchpad clean per ``rules.md`` §1.3 (mandatory teardown).

Safety model
------------
* **Dry-run by default.** Nothing is removed unless ``--apply`` is passed.
* Only directories directly under ``03_workspace/`` whose name matches
  ``<TASK_ID>_<repo>`` (e.g. ``T-010_intel_project_template``) are ever
  considered. Files and unrelated directories are left untouched.
* Git worktrees are removed via ``git worktree remove`` so Git bookkeeping stays
  consistent. A *dirty* worktree (uncommitted changes) is skipped unless
  ``--force`` is given.
* A workspace that is a plain directory (not a registered worktree) is only
  deleted when ``--force`` is supplied.

Exit code is non-zero if any planned removal could not be completed.

Usage::

    python3 scripts/prune_workspace.py            # dry-run, show the plan
    python3 scripts/prune_workspace.py --apply     # perform safe removals
    python3 scripts/prune_workspace.py --apply --force
    python3 scripts/prune_workspace.py --root /path/to/project
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

TASK_ID_RE = re.compile(r"^(T-\d+)")
FRONTMATTER_ID_RE = re.compile(r"^id:\s*['\"]?(T-\d+)", re.MULTILINE)


def find_project_root(start: Path) -> Path | None:
    """Return the nearest ancestor (or ``start``) containing the Kanban dirs."""
    for candidate in [start, *start.parents]:
        if (candidate / "02_tasks").is_dir() and (candidate / "03_workspace").is_dir():
            return candidate
    return None


def completed_task_ids(done_dir: Path) -> set[str]:
    """Collect task IDs from files in ``02_tasks/3_done/``.

    Prefers the YAML ``id:`` field; falls back to the filename prefix.
    """
    ids: set[str] = set()
    if not done_dir.is_dir():
        return ids
    for md in sorted(done_dir.glob("*.md")):
        text = md.read_text(encoding="utf-8", errors="replace")
        match = FRONTMATTER_ID_RE.search(text)
        if match:
            ids.add(match.group(1))
            continue
        name_match = TASK_ID_RE.match(md.name)
        if name_match:
            ids.add(name_match.group(1))
    return ids


def workspace_entries(workspace_dir: Path) -> list[tuple[str, Path]]:
    """Return ``(task_id, path)`` for each ``<TASK_ID>_<repo>`` directory."""
    entries: list[tuple[str, Path]] = []
    if not workspace_dir.is_dir():
        return entries
    for child in sorted(workspace_dir.iterdir()):
        if not child.is_dir():
            continue
        match = TASK_ID_RE.match(child.name)
        if match:
            entries.append((match.group(1), child))
    return entries


def is_git_worktree(path: Path) -> bool:
    """A linked worktree carries a ``.git`` *file* (a gitlink), not a dir."""
    return (path / ".git").is_file()


def worktree_is_dirty(path: Path) -> bool:
    """True if the worktree has uncommitted changes (or state is unknown)."""
    result = subprocess.run(
        ["git", "-C", str(path), "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # If we cannot determine cleanliness, treat as dirty (fail safe).
        return True
    return bool(result.stdout.strip())


def remove_worktree(root: Path, path: Path, force: bool) -> tuple[bool, str]:
    """Remove a git worktree. Returns ``(ok, message)``."""
    cmd = ["git", "-C", str(root), "worktree", "remove"]
    if force:
        cmd.append("--force")
    cmd.append(str(path))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        subprocess.run(
            ["git", "-C", str(root), "worktree", "prune"],
            capture_output=True,
            text=True,
        )
        return True, "removed worktree"
    return False, (result.stderr or result.stdout).strip()


def remove_plain_dir(path: Path, force: bool) -> tuple[bool, str]:
    if not force:
        return False, "plain directory; re-run with --force to delete"
    shutil.rmtree(path)
    return True, "removed directory"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prune 03_workspace/ entries for completed (3_done) tasks.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually perform removals (default is a dry-run).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force removal of dirty worktrees / plain directories.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Project root (auto-detected from CWD/script location if omitted).",
    )
    args = parser.parse_args(argv)

    root = (
        args.root
        or find_project_root(Path.cwd())
        or find_project_root(Path(__file__).resolve().parent)
    )
    if root is None:
        print(
            "error: could not locate a project root containing 02_tasks/ and "
            "03_workspace/ (use --root)",
            file=sys.stderr,
        )
        return 2
    root = root.resolve()

    done_ids = completed_task_ids(root / "02_tasks" / "3_done")
    entries = workspace_entries(root / "03_workspace")

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] project root: {root}")
    print(f"completed tasks (3_done): {', '.join(sorted(done_ids)) or '(none)'}")

    to_prune = [(tid, path) for tid, path in entries if tid in done_ids]
    retained = [(tid, path) for tid, path in entries if tid not in done_ids]

    for tid, path in retained:
        print(f"  keep    {path.name}  ({tid} not in 3_done)")

    if not to_prune:
        print("nothing to prune.")
        return 0

    failures = 0
    for tid, path in to_prune:
        rel = path.relative_to(root)
        if not args.apply:
            kind = "worktree" if is_git_worktree(path) else "directory"
            print(f"  prune   {rel}  ({tid} done) -> would remove {kind}")
            continue

        if is_git_worktree(path):
            if not args.force and worktree_is_dirty(path):
                print(
                    f"  SKIP    {rel}  ({tid}) -> worktree has uncommitted "
                    "changes; re-run with --force"
                )
                failures += 1
                continue
            ok, msg = remove_worktree(root, path, args.force)
        else:
            ok, msg = remove_plain_dir(path, args.force)

        status = "pruned " if ok else "FAILED "
        print(f"  {status} {rel}  ({tid}) -> {msg}")
        if not ok:
            failures += 1

    if failures:
        print(f"done with {failures} unresolved item(s).", file=sys.stderr)
        return 1
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
