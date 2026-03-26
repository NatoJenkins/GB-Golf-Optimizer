---
phase: 11-deploy-and-verification
plan: 01
subsystem: infra
tags: [postgresql, sqlite, pragma, deploy, flask-migrate, dialect]

# Dependency graph
requires:
  - phase: 09-fetch-pipeline
    provides: "fetcher.py write_projections function with PRAGMA statement"
  - phase: 08-database
    provides: "Flask-SQLAlchemy db setup with PostgreSQL/SQLite support"
provides:
  - "PostgreSQL-safe write_projections() with dialect-conditional PRAGMA"
  - "deploy.sh with sync -> migrate -> restart pipeline"
  - ".venv exclusion from deploy tar"
affects: [11-02-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns: ["dialect-conditional SQL for cross-database safety"]

key-files:
  created: []
  modified: [gbgolf/fetcher.py, deploy/deploy.sh, tests/test_fetcher.py]

key-decisions:
  - "Used session.get_bind().dialect.name instead of session.bind.dialect.name for Flask-SQLAlchemy scoped session compatibility"

patterns-established:
  - "Dialect guard: always check session.get_bind().dialect.name before dialect-specific SQL"

requirements-completed: [FETCH-01, FETCH-02, FETCH-03, FETCH-04, FETCH-05, FETCH-06]

# Metrics
duration: 4min
completed: 2026-03-26
---

# Phase 11 Plan 01: PRAGMA PostgreSQL Fix + Deploy Migration Step Summary

**Dialect-guarded PRAGMA foreign_keys for PostgreSQL safety, deploy.sh with flask db upgrade migration step between sync and restart**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-26T02:18:38Z
- **Completed:** 2026-03-26T02:22:38Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Fixed PRAGMA foreign_keys = ON to only execute on SQLite, preventing ProgrammingError on PostgreSQL
- Added flask db upgrade migration step to deploy.sh between file sync and service restart
- Added .venv exclusion to deploy tar command and updated URL to https
- Added dialect-conditional PRAGMA test verifying non-sqlite dialects skip the statement

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix PRAGMA foreign_keys to be PostgreSQL-safe** - `b1c9948` (test: RED), `ca16b7d` (feat: GREEN)
2. **Task 2: Update deploy.sh with migration step and .venv exclusion** - `5e45f91` (feat)

**Plan metadata:** [pending] (docs: complete plan)

_Note: Task 1 used TDD with RED-GREEN commits_

## Files Created/Modified
- `gbgolf/fetcher.py` - Added dialect guard around PRAGMA foreign_keys = ON in write_projections()
- `deploy/deploy.sh` - Added .venv exclusion, flask db upgrade step, https URL
- `tests/test_fetcher.py` - Added dialect-conditional PRAGMA test + clarifying comments on existing PRAGMA lines

## Decisions Made
- Used `session.get_bind().dialect.name` instead of `session.bind.dialect.name` because Flask-SQLAlchemy's scoped session returns None for `.bind` attribute but `.get_bind()` correctly resolves the engine

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Used get_bind() instead of .bind for dialect check**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Plan specified `session.bind.dialect.name` but Flask-SQLAlchemy's scoped session has `.bind = None`, causing AttributeError
- **Fix:** Changed to `session.get_bind().dialect.name` which correctly resolves the engine
- **Files modified:** gbgolf/fetcher.py
- **Verification:** All 116 tests pass
- **Committed in:** ca16b7d (Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix for Flask-SQLAlchemy compatibility. No scope creep.

## Issues Encountered
None beyond the deviation noted above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- fetcher.py is PostgreSQL-safe, ready for production deployment
- deploy.sh has the correct sync -> migrate -> restart order
- All 116 tests pass, full test suite green
- Ready for 11-02 plan (deployment execution)

## Self-Check: PASSED

All files found. All commits verified (b1c9948, ca16b7d, 5e45f91).

---
*Phase: 11-deploy-and-verification*
*Completed: 2026-03-26*
