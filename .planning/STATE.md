---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Manual Lock/Exclude
status: completed
stopped_at: Completed 07-02-PLAN.md
last_updated: "2026-03-14T20:24:39.646Z"
last_activity: "2026-03-14 — Plan 07-01 complete: UI-05/UI-06 constraint count div + updateConstraintCount() JS wired; 4 new tests GREEN, sort headers RED scaffold for Plan 02"
progress:
  total_phases: 4
  completed_phases: 4
  total_plans: 10
  completed_plans: 10
  percent: 90
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-14)

**Core value:** Generate the best possible cash contest lineups from the user's available player cards, maximizing expected score within salary and collection constraints.
**Current focus:** Phase 7 in progress — Plan 01 complete (UI-05/UI-06 constraint count), Plan 02 (sort headers) remaining

## Current Position

Phase: 7 of 7 (Polish) — In Progress
Plan: 1 of 2 complete (Plan 01 done — constraint count display + 5 new tests; Plan 02 sort headers remaining)
Status: Phase 7 Plan 01 complete — constraint count div and JS wired; test_sort_headers_rendered RED scaffold ready for Plan 02
Last activity: 2026-03-14 — Plan 07-01 complete: UI-05/UI-06 constraint count div + updateConstraintCount() JS wired; 4 new tests GREEN, sort headers RED scaffold for Plan 02

Progress: [█████████░] 90% (9/10 plans done)

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
- [Phase 06]: _parse_card_keys() defined inline in reoptimize() to keep helper co-located with its only caller
- [Phase 06]: check_feasibility called per contest config in a loop; ConstraintSet built from parsed form values directly (not session re-read)
- [Phase 06-lock-exclude-ui]: Lock column renders lock icon via Jinja2 set membership against locked_card_keys; tfoot colspan bumped from 2 to 3
- [Phase 07-polish]: constraint-count element inside show_results block; .lock-golfer-cb listener added; test_sort_headers_rendered intentionally RED for Plan 02
- [Phase 07-polish]: th.textContent setter used for sort indicator updates — safe because onclick is an HTML attribute not a JS child node property
- [Phase 07-polish]: data-sort uses raw values (no dollar prefix for salary, 0/1 for checkboxes) enabling parseFloat numeric sort

### Pending Todos

None.

### Blockers/Concerns

None — Phase 4 multi-lineup lock semantics resolved via fires-once tracking.

## Session Continuity

Last session: 2026-03-14T20:21:48.605Z
Stopped at: Completed 07-02-PLAN.md
Resume file: None
