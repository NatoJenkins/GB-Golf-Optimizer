---
phase: 10-projection-source-selector
plan: 02
subsystem: ui
tags: [flask, jinja2, css, javascript, radio-buttons, staleness-label, tdd]

# Dependency graph
requires:
  - phase: 10-projection-source-selector
    provides: load_projections_from_db(), validate_pipeline_auto(), _db_template_vars(), source-aware GET/POST routes
  - phase: 09-datagolf-fetcher
    provides: DB populated with projection data via fetch CLI command
provides:
  - Source selector radio buttons (Auto / Upload CSV) in index.html
  - Staleness label showing tournament name and relative fetch age
  - Disabled Auto state with "No projections available yet" when DB empty
  - JS toggle hiding/showing projections upload zone based on source selection
  - CSS classes for source selector, staleness label, disabled opacity
  - 8 new test functions covering SRC-01 through SRC-05
  - db_client fixture and _seed_projections helper for DB-backed web tests
affects: [11-deployment]

# Tech tracking
tech-stack:
  added: []
  patterns: [radio-button source toggle with hidden input, conditional required attribute, JS DOM toggle for form zone visibility]

key-files:
  created: []
  modified:
    - gbgolf/web/templates/index.html
    - gbgolf/web/static/style.css
    - gbgolf/web/routes.py
    - tests/test_web.py

key-decisions:
  - "Conditional required attribute on projections file input -- only required when CSV source active, prevents HTML5 validation blocking Auto submissions"
  - "Hidden input projection_source synced by JS from radio buttons -- form submission always includes source value regardless of radio button state"

patterns-established:
  - "db_client fixture pattern: Flask test client with _app stash for DB seeding access in test helpers"
  - "_seed_projections() helper: reusable DB seeding for web tests needing fetches + projections data"
  - "Radio button + hidden input pattern: user-facing radios drive a hidden input for form submission"

requirements-completed: [SRC-01, SRC-03, SRC-05]

# Metrics
duration: 4min
completed: 2026-03-26
---

# Phase 10 Plan 02: Source Selector UI & Test Suite Summary

**Radio button source selector (Auto/CSV) with staleness label, JS toggle for projections zone visibility, conditional required attribute, dark-theme CSS, and 8 TDD tests covering SRC-01 through SRC-05**

## Performance

- **Duration:** 4 min (across two sessions with visual verification checkpoint)
- **Started:** 2026-03-26T00:48:00Z
- **Completed:** 2026-03-26T01:00:00Z
- **Tasks:** 2 (1 TDD auto + 1 human-verify checkpoint)
- **Files modified:** 4

## Accomplishments
- Added source selector radio buttons (Auto / Upload CSV) as first form-row in upload section with conditional checked/disabled state based on db_has_projections
- Added staleness label showing tournament name and relative fetch age ("fetched N days ago"), with stale styling via CSS
- Added JS toggle that hides/shows projections upload zone, manages required attribute, and clears file input when switching to Auto
- Added CSS classes (.source-selector, .source-radio, .staleness-label) matching UI-SPEC spacing tokens (16px gap, 0.75rem radio font, 0.62rem staleness font, 0.35 disabled opacity)
- Added 8 new test functions with db_client fixture and _seed_projections helper, all passing green
- User visually verified dark theme rendering, radio toggle behavior, and lineup generation from DB projections

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Add failing test suite for source selector** - `51d925e` (test)
2. **Task 1 (GREEN): Add source selector UI to template and CSS** - `145fe6c` (feat)
3. **Task 2: Visual verification** - No commit (human-verify checkpoint, user approved)

**Plan metadata:** (pending)

## Files Created/Modified
- `gbgolf/web/templates/index.html` - Added source selector form-row with radio buttons, hidden input, staleness label, projections-zone wrapper, JS toggle script
- `gbgolf/web/static/style.css` - Added .source-selector, .source-radio, .source-radio:has(input[disabled]), .staleness-label, .staleness-label.stale
- `gbgolf/web/routes.py` - Minor fix for db_has_projections context variable
- `tests/test_web.py` - Added db_client fixture, _seed_projections helper, 8 new test functions (test_source_selector_rendered through test_auto_source_unmatched_players)

## Decisions Made
- Conditional required attribute on projections file input: only set when CSV is active source, preventing HTML5 validation from blocking Auto-source form submissions
- Hidden input projection_source synced by JS from radio buttons: ensures form always submits the source value even if radios are in different states

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 10 complete: full source selector feature delivered (backend Plan 01 + frontend Plan 02)
- All SRC requirements (SRC-01 through SRC-05) satisfied
- Ready for Phase 11: Deploy and Verification on production VPS
- Both projection sources (Auto DB and Upload CSV) produce correct optimizer results

## Self-Check: PASSED

All 5 claimed files exist. Both task commits (51d925e, 145fe6c) verified in git log.

---
*Phase: 10-projection-source-selector*
*Completed: 2026-03-26*
