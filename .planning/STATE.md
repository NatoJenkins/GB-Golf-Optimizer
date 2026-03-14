---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Manual Lock/Exclude
status: in-progress
stopped_at: Completed 04-01-PLAN.md
last_updated: "2026-03-14T07:51:00.000Z"
last_activity: 2026-03-14 — Phase 4 Plan 01 complete (ConstraintSet module)
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 3
  completed_plans: 1
  percent: 8
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-14)

**Core value:** Generate the best possible cash contest lineups from the user's available player cards, maximizing expected score within salary and collection constraints.
**Current focus:** Phase 4 — Constraint Foundation

## Current Position

Phase: 4 of 7 (Constraint Foundation)
Plan: 2 of 3 (next: 04-02-PLAN.md — engine ILP constraints)
Status: In progress
Last activity: 2026-03-14 — Plan 04-01 complete: ConstraintSet module and unit tests

Progress: [█░░░░░░░░░] 8% (v1.1, 1/3 Phase 4 plans done)

## Accumulated Context

### Decisions

All key decisions logged in PROJECT.md Key Decisions table.

Recent decisions affecting current work:
- Session architecture: Lock/exclude identifiers stored in Flask built-in cookie session (fits comfortably under 4KB). Card objects NOT stored in session — serialized to hidden form field instead.
- Stable card key: Use composite (player, salary, multiplier, collection) key rather than Python id() — id() breaks across requests.
- No new dependencies: Flask session + PuLP += constraint API + Jinja2 checkboxes covers all v1.1 needs without additions.
- PreSolveError is a return-object (not exception): callers check if result is None or PreSolveError instance.
- check_conflicts runs before check_feasibility (documented in module docstring as contract).
- Golfer locks are ILP-level constraints (engine.py), not pre-solve. check_feasibility only inspects locked_cards.

### Pending Todos

None.

### Blockers/Concerns

- Phase 4 risk: Lock constraint semantics in the multi-lineup sequential loop. Card-level locks can only fire once (card consumed). Golfer-level locks may become infeasible in lineup 2+ if golfer has only one card. See PITFALLS.md for full checklist.

## Session Continuity

Last session: 2026-03-14T07:51:00.000Z
Stopped at: Completed 04-01-PLAN.md
Resume file: .planning/phases/04-constraint-foundation/04-02-PLAN.md
