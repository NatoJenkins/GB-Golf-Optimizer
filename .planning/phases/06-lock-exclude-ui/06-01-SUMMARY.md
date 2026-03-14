---
phase: 06-lock-exclude-ui
plan: 01
subsystem: testing
tags: [pytest, flask, tdd, red-tests, player-pool, lock-exclude]

# Dependency graph
requires:
  - phase: 05-serialization-and-re-optimize-route
    provides: _build_card_pool_json helper, /reoptimize route, client fixture, _post_csvs helper
provides:
  - 10 failing RED test functions specifying Phase 6 UI behaviours (UI-01 and UI-03)
  - Test coverage for player pool section rendering, checkbox form fields, route parsing, lock column
affects:
  - 06-02 (player pool table + checkbox implementation must turn these GREEN)
  - 06-03 (lock column implementation must turn UI-03 tests GREEN)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD RED phase: write failing tests before implementation; assert AssertionError not ImportError"
    - "Session inspection via client.session_transaction() after POST to verify route writes"
    - "Pipe-delimited composite key format for checkbox values: player|salary|multiplier|collection"

key-files:
  created: []
  modified:
    - tests/test_web.py

key-decisions:
  - "test_nonlocked_card_blank_lock_column asserts <th>Lock</th> header presence to stay RED (the header alone makes it fail today, matching the 10-test RED requirement)"
  - "Lock icon tested as Unicode escape \\U0001f512 rather than raw emoji for portability in assert strings"

patterns-established:
  - "Phase 06 tests appended in two named sections: '# Phase 06: UI-01' and '# Phase 06: UI-03'"
  - "Route-parsing tests read session state via client.session_transaction() immediately after response"

requirements-completed: [UI-01, UI-03]

# Metrics
duration: 10min
completed: 2026-03-14
---

# Phase 06 Plan 01: Lock/Exclude UI — TDD RED Suite Summary

**10 failing test functions added to tests/test_web.py specifying player pool table rendering, checkbox form encoding, route-level lock/exclude parsing, and lineup Lock column — all RED before any Phase 6 implementation.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-03-14
- **Completed:** 2026-03-14
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Added 7 UI-01 RED tests covering player pool section, table column headers, lock/exclude/golfer checkboxes inside reoptimize-form, and /reoptimize route parsing of all three checkbox field types
- Added 3 UI-03 RED tests covering lineup lock column header, lock icon on locked-card rows, and blank lock cells when no cards are locked
- All 17 prior tests (Phase 3-5) remain GREEN; all 10 new tests fail with AssertionError only

## Task Commits

Each task was committed atomically:

1. **Task 1: Add UI-01 test functions** - `3f41a1a` (test)
2. **Task 2: Add UI-03 test functions** - `32460c6` (test)

## Files Created/Modified
- `tests/test_web.py` — 10 new test functions appended under Phase 06 UI-01 and UI-03 section comments

## Decisions Made
- `test_nonlocked_card_blank_lock_column` asserts both `<th>Lock</th>` presence AND absence of lock icon. The double-assertion keeps it RED today (header not yet present) and guards correctness after Plan 03 (icon must not appear when nothing is locked).
- Lock icon verified as `\U0001f512` (Unicode escape) rather than a raw emoji character to avoid encoding edge-cases in assert strings.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `test_nonlocked_card_blank_lock_column` as initially written was trivially GREEN (no icon = passes without any implementation). Corrected by adding the `<th>Lock</th>` header assertion, making the test properly RED while still expressing the correct post-implementation contract.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- RED suite is in place; Plan 02 can implement player pool table + checkbox rendering to turn UI-01 tests GREEN
- Plan 03 can implement lineup lock column to turn UI-03 tests GREEN
- No blockers

---
*Phase: 06-lock-exclude-ui*
*Completed: 2026-03-14*
