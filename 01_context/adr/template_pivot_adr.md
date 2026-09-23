# ADR-00X: <Concise pivot title>

> **Pivot ADR template.** Copy this file to `01_context/adr/00X-<slug>.md` (use the
> next free number) and fill in every section. Use this template whenever a change
> invalidates an accepted ADR or materially redirects the project. Do **not** edit
> the superseded ADR's Decision in place — link to it below and set its Status to
> `Superseded by ADR-00X`.

## Status

Proposed <!-- Proposed → Accepted once ratified. Later, if reversed: Superseded by ADR-00Y -->

## Supersedes

- ADR-00Y — `<one-line title>` (set that ADR's Status to `Superseded by ADR-00X`).
- _List every accepted ADR this pivot invalidates; "None" if this is net-new._

## Trigger

What forced the pivot? Name the concrete event, constraint, or discovery — a
failing assumption, a blocked dependency, a new requirement, a security or
performance finding — and the date it surfaced. State plainly which accepted
decision(s) it invalidates and why the previous direction is no longer viable.

## Blast Radius

What this pivot touches, so nothing is silently dropped:

- **Code / artifacts:** repositories, modules, scripts, or docs affected.
- **Tasks:** in-flight and backlog tasks that must be reshaped, split, re-ordered,
  or cancelled (list task IDs).
- **Interfaces / contracts:** downstream child repos or derived projects impacted;
  note any migration steps required to preserve backward compatibility.
- **Other ADRs:** decisions weakened or invalidated alongside the primary one.

## New Direction (Decision)

State the new decision as clearly and testably as the ADR it replaces. Make the
boundary unambiguous by also naming what is explicitly **out of scope**.

## Backlog-Evolution Strategy

How the backlog changes as a direct result of this pivot:

- **Create:** new tasks (IDs, dependencies, target repos).
- **Re-scope / re-order:** existing tasks whose scope or dependencies change (keep
  the dependency graph acyclic per `rules.md` §1.4).
- **Cancel / defer:** tasks no longer needed (annotate/move rather than delete;
  record why).
- **Dashboard:** the `00_DASHBOARD.md` updates required to reflect all of the above.

## Consequences

### Pros

- ...

### Cons / Risks

- ...

## Notes

This ADR is itself immutable once accepted. A future reversal supersedes it with a
new numbered ADR rather than editing it in place.
