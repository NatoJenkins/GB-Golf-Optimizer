---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Manual Lock/Exclude
status: in_progress
stopped_at: Completed 06-01-PLAN.md
last_updated: "2026-03-14T18:30:00.000Z"
last_activity: "2026-03-14 — Plan 06-01 complete: 10 failing RED tests for Phase 6 UI behaviours (player pool table, checkboxes, lock column)"
progress:
  total_phases: 4
  completed_phases: 2
  total_plans: 8
  completed_plans: 6
  percent: 75
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-14)

**Core value:** Generate the best possible cash contest lineups from the user's available player cards, maximizing expected score within salary and collection constraints.
**Current focus:** Phase 6 — Lock/Exclude UI (Plan 01 complete, Plans 02-03 pending)

## Current Position

Phase: 6 of 7 (Lock/Exclude UI) — In Progress
Plan: 1 of 3 complete (Plan 01 done — RED tests; Plan 02, Plan 03 pending)
Status: Phase 6 Plan 01 complete — ready for Plan 02
Last activity: 2026-03-14 — Plan 06-01 complete: 10 failing RED tests for Phase 6 UI behaviours (player pool table, checkboxes, lock column)

Progress: [███████▌░░] 75% (v1.1, 1/3 Phase 6 plans done)

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
- [Phase 05-serialization-and-re-optimize-route]: Card pool stored as JSON in hidden form field rather than Flask session (avoids 4KB cookie limit)
- [Phase 05-serialization-and-re-optimize-route]: Two button-rendering tests intentionally RED until Plan 02 adds template changes
- [Phase 05-serialization-and-re-optimize-route]: Re-Optimize form uses | e filter (HTML-entity-escape) for card_pool JSON in attribute context; null-guarded JS listener handles conditional DOM element
- [Phase 05-serialization-and-re-optimize-route]: Hidden card_pool carried in both standalone #card-pool-data input and inside #reoptimize-form for belt-and-suspenders extensibility
- [Phase 06-lock-exclude-ui]: test_nonlocked_card_blank_lock_column asserts both Lock header presence AND no icon — double assertion keeps test RED today and guards correctness post-Plan 03
- [Phase 06-lock-exclude-ui]: Lock icon verified as \U0001f512 Unicode escape in test assert strings for encoding portability

### Pending Todos

None.

### Blockers/Concerns

None — Phase 4 multi-lineup lock semantics resolved via fires-once tracking.

## Session Continuity

Last session: 2026-03-14T18:30:00.000Z
Stopped at: Completed 06-01-PLAN.md
Resume file: .planning/phases/06-lock-exclude-ui/06-02-PLAN.md
