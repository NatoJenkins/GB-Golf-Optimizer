---
phase: 05-serialization-and-re-optimize-route
plan: "01"
subsystem: ui
tags: [flask, json, serialization, optimizer, tdd]

# Dependency graph
requires:
  - phase: 04-constraint-foundation
    provides: ConstraintSet, session lock/exclude integration, Flask session architecture
provides:
  - _serialize_cards helper: converts list[Card] to JSON string for hidden form field
  - _deserialize_cards helper: reconstructs list[Card] from JSON string
  - POST /reoptimize route: re-runs optimizer using serialized card pool + session constraints
  - card_pool_json kwarg added to upload route render_template
affects:
  - 05-02 (template changes to add reoptimize button form)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Card round-trip serialization via JSON hidden form field (avoids Flask session 4KB limit)"
    - "TDD RED/GREEN discipline: 7 tests written before implementation, 5 green in Plan 01"
    - "Error path returns session-expired message for missing/malformed card_pool"

key-files:
  created: []
  modified:
    - gbgolf/web/routes.py
    - tests/test_web.py

key-decisions:
  - "Card pool stored in hidden form field (JSON), not Flask session — avoids 4KB cookie limit"
  - "2 button-rendering tests stay RED intentionally — template changes deferred to Plan 02"
  - "Error message is 'Session expired — please re-upload your files' for both missing and malformed card_pool"

patterns-established:
  - "_serialize_cards/_deserialize_cards: module-level helpers before blueprint definition"
  - "reoptimize route reads locked_cards/excluded_cards from session, not from request"

requirements-completed: [UI-02]

# Metrics
duration: 2min
completed: 2026-03-14
---

# Phase 5 Plan 01: Card Pool Serialization and POST /reoptimize Route Summary

**JSON hidden-form-field serialization helpers and POST /reoptimize route enabling constraint iteration without file re-upload**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-14T08:25:41Z
- **Completed:** 2026-03-14T08:27:45Z
- **Tasks:** 2 (RED + GREEN)
- **Files modified:** 2

## Accomplishments

- Wrote all 7 test stubs up front (RED phase) — confirmed 404 failures before any implementation
- Implemented `_serialize_cards` and `_deserialize_cards` module-level helpers in routes.py
- Added POST /reoptimize route that deserializes card pool, reads session constraints, and re-runs optimizer
- Modified upload route render_template to pass `card_pool_json` kwarg
- 5 of 7 new tests GREEN; 2 template tests intentionally RED (pending Plan 02)
- Full 66-test suite unbroken (excluding 2 known RED button tests)

## Task Commits

Each task was committed atomically:

1. **RED phase: 7 failing test stubs** - `c01531e` (test)
2. **GREEN phase: serialization helpers + /reoptimize route** - `af710ae` (feat)

## Files Created/Modified

- `gbgolf/web/routes.py` - Added `json`/`date`/`Card` imports, `_serialize_cards`, `_deserialize_cards`, modified upload render_template, added POST /reoptimize route
- `tests/test_web.py` - Appended 7 new test functions: `test_reoptimize_returns_results`, `test_reoptimize_layout_identical`, `test_reoptimize_missing_card_pool`, `test_reoptimize_malformed_card_pool`, `test_reoptimize_uses_session_constraints`, `test_reoptimize_button_rendered`, `test_reoptimize_button_absent_on_get`

## Decisions Made

- Card pool stored as JSON in hidden form field rather than Flask session (cookie 4KB limit would be exceeded by large card pools)
- Two button-rendering tests (`test_reoptimize_button_rendered`, `test_reoptimize_button_absent_on_get`) intentionally remain RED — template changes belong in Plan 02, not here
- Error message "Session expired — please re-upload your files" used for both missing and malformed `card_pool` field — consistent UX signal

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- POST /reoptimize backend is complete and tested
- Plan 02 needs to add `id="reoptimize-form"` hidden form with `card_pool` field to `index.html` template
- The 2 intentionally RED tests (`test_reoptimize_button_rendered`, `test_reoptimize_button_absent_on_get`) will turn GREEN once Plan 02 template changes are in place

---
*Phase: 05-serialization-and-re-optimize-route*
*Completed: 2026-03-14*

## Self-Check: PASSED

- `gbgolf/web/routes.py` - FOUND
- `tests/test_web.py` - FOUND
- `.planning/phases/05-serialization-and-re-optimize-route/05-01-SUMMARY.md` - FOUND
- Commit `c01531e` (RED phase tests) - FOUND
- Commit `af710ae` (GREEN phase implementation) - FOUND
