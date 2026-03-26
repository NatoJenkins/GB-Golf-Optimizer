---
phase: 10-projection-source-selector
plan: 01
subsystem: api
tags: [flask, sqlalchemy-core, db-query, projection-source, routes]

# Dependency graph
requires:
  - phase: 08-database-foundation
    provides: fetches + projections DB tables, db.session.execute(text()) pattern
  - phase: 09-datagolf-fetcher
    provides: DB populated with projection data via fetch CLI command
provides:
  - load_projections_from_db() function returning dict[str, float] with normalized name keys
  - validate_pipeline_auto() function using DB projections instead of CSV
  - Source-aware GET route passing db_has_projections and latest_fetch to template
  - Source-aware POST route branching on projection_source (auto vs csv)
  - _get_latest_fetch() helper with staleness calculation
  - _db_template_vars() convenience function for all render_template calls
affects: [10-02-PLAN (frontend integration), 11-deployment]

# Tech tracking
tech-stack:
  added: []
  patterns: [DB query helper for template context, source-aware route branching]

key-files:
  created: []
  modified:
    - gbgolf/data/__init__.py
    - gbgolf/web/routes.py
    - tests/test_web.py

key-decisions:
  - "Separate validate_pipeline_auto() function rather than modifying existing validate_pipeline() -- avoids risk to CSV path"
  - "DB template vars injected via _db_template_vars() helper called in every render_template -- prevents Pitfall 5 (missing context on error)"
  - "Staleness threshold: 7 days (is_stale flag) -- per CONTEXT.md locked decision"

patterns-established:
  - "_db_template_vars() pattern: all render_template calls include DB context for source selector state"
  - "_get_latest_fetch() pattern: timezone-safe staleness calculation handling both SQLite (naive) and PostgreSQL (aware) datetimes"

requirements-completed: [SRC-02, SRC-04]

# Metrics
duration: 3min
completed: 2026-03-26
---

# Phase 10 Plan 01: Backend Data Layer & Route Logic Summary

**DB projection loading via load_projections_from_db() with normalize_name(), validate_pipeline_auto() variant, and source-aware GET/POST routes passing db_has_projections + latest_fetch to all template renders**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-26T00:41:19Z
- **Completed:** 2026-03-26T00:44:56Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Added load_projections_from_db() that queries latest fetch, reads projections, and normalizes player names for match_projections() compatibility
- Added validate_pipeline_auto() that replaces only the projections-loading step while keeping roster parsing, filtering, and pool-size guard identical to CSV path
- Modified GET / to query DB for latest fetch info (tournament name, days ago, staleness) and pass to template
- Modified POST / to branch on projection_source field: "auto" uses DB projections, "csv" preserves existing file upload path unchanged
- Added **_db_template_vars() to all 10 render_template calls across index() and reoptimize()

## Task Commits

Each task was committed atomically:

1. **Task 1: Add load_projections_from_db and validate_pipeline_auto to data layer** - `ae809d2` (feat)
2. **Task 2: Modify routes for source-aware GET and POST** - `98724f5` (feat)

## Files Created/Modified
- `gbgolf/data/__init__.py` - Added load_projections_from_db(), validate_pipeline_auto(), updated __all__ exports, added sqlalchemy text and db imports
- `gbgolf/web/routes.py` - Added _get_latest_fetch(), _db_template_vars(), source-aware GET/POST handling, **_db_template_vars() on all render_template calls
- `tests/test_web.py` - Fixed client fixture to create DB tables (fetches/projections) for test database

## Decisions Made
- Separate validate_pipeline_auto() function rather than modifying existing validate_pipeline() -- avoids any risk to the working CSV path (per RESEARCH.md anti-pattern guidance)
- _db_template_vars() helper called in every render_template rather than computing once at top of handler -- ensures error paths never miss DB context (Pitfall 5 prevention)
- Staleness threshold locked at 7 days per CONTEXT.md decision

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed test_web.py client fixture missing DB table creation**
- **Found during:** Task 2 (verification step)
- **Issue:** Existing test_web.py `client` fixture did not call `_db.create_all()`, so the fetches table didn't exist in the test SQLite database. All web tests failed with `OperationalError: no such table: fetches` because _get_latest_fetch() now queries fetches on every request.
- **Fix:** Updated client fixture to import db, wrap test client in app_context, call _db.create_all() before yield and _db.drop_all() after.
- **Files modified:** tests/test_web.py
- **Verification:** All 32 web tests pass; full suite of 107 tests green.
- **Committed in:** 98724f5 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential fix for test infrastructure compatibility with new DB queries. No scope creep.

## Issues Encountered
None beyond the auto-fixed test fixture issue.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Backend contract complete: GET / passes db_has_projections and latest_fetch, POST / branches on projection_source
- Plan 02 (frontend) can now add radio buttons, staleness label, JS toggle, and CSS styling
- Template variables db_has_projections (bool) and latest_fetch (dict or None) are available in every render

---
*Phase: 10-projection-source-selector*
*Completed: 2026-03-26*
