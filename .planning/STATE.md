---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Manual Lock/Exclude
status: executing
stopped_at: Completed 04-03-PLAN.md
last_updated: "2026-03-14T07:39:51.736Z"
last_activity: "2026-03-14 — Plan 04-03 complete: Flask session integration, reset banner, 3 integration tests"
progress:
  total_phases: 4
  completed_phases: 1
  total_plans: 3
  completed_plans: 3
  percent: 18
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-14)

**Core value:** Generate the best possible cash contest lineups from the user's available player cards, maximizing expected score within salary and collection constraints.
**Current focus:** Phase 4 — Constraint Foundation

## Current Position

Phase: 4 of 7 (Constraint Foundation) — COMPLETE
Plan: 3 of 3 — all complete
Status: Complete
Last activity: 2026-03-14 — Plan 04-03 complete: Flask session integration, reset banner, 3 integration tests

Progress: [██████████] 100% (v1.1, 3/3 Phase 4 plans done)

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
- Golfer-lock fires once globally: discard from unsatisfied_golfer_locks after first placement to prevent lineup 2+ infeasibility.
- Card-lock fires once: discard from active_card_locks after placement (used_card_keys already prevents reuse).
- Excludes are pre-filters applied to available pool per iteration, not ILP constraints.
- Composite key (player, salary, multiplier, collection) replaces id() for stable cross-request card identity.
- [Phase 04-constraint-foundation]: Session clear is unconditional on file upload (no hash comparison) — simplicity over incremental invalidation
- [Phase 04-constraint-foundation]: Session clear before ConstraintSet build so new ConstraintSet always reflects cleared state (order: clear -> build -> optimize)

### Pending Todos

None.

### Blockers/Concerns

None — Phase 4 multi-lineup lock semantics resolved via fires-once tracking.

## Session Continuity

Last session: 2026-03-14T07:39:51.732Z
Stopped at: Completed 04-03-PLAN.md
Resume file: None
