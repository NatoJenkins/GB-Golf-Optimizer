---
phase: 04-constraint-foundation
plan: "03"
subsystem: ui
tags: [flask, session, jinja2, constraints, integration-tests]

# Dependency graph
requires:
  - phase: 04-constraint-foundation/04-01
    provides: ConstraintSet dataclass and pre-solve check functions
  - phase: 04-constraint-foundation/04-02
    provides: optimize() accepting constraints= kwarg with ILP enforcement
provides:
  - Flask SECRET_KEY configured in create_app() enabling cookie session
  - Session read/write for lock/exclude state in routes.py
  - Session clear on file upload (unconditional, before ConstraintSet build)
  - ConstraintSet constructed from session and passed to optimize()
  - Reset banner in index.html rendered when lock_reset=True
  - Integration tests for session clearing and banner rendering (3 new tests)
affects:
  - Phase 5 (lock/exclude UI — session keys are now readable/writable from routes)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Flask cookie session for persisting lock/exclude state across requests
    - Session clear before ConstraintSet build (clear -> build -> optimize order)
    - Jinja2 conditional banner for transient action feedback
    - TDD RED/GREEN for integration tests against Flask test client

key-files:
  created: []
  modified:
    - gbgolf/web/__init__.py
    - gbgolf/web/routes.py
    - gbgolf/web/templates/index.html
    - tests/test_web.py

key-decisions:
  - "Session clear is unconditional on file upload (no hash comparison) — simplicity over incremental invalidation"
  - "Session clear happens BEFORE ConstraintSet build so the new ConstraintSet always reflects cleared state"
  - "lock_reset flag passed as template variable; banner placed inside show_results block so it only shows after successful optimization"
  - "check_conflicts and check_feasibility imported into routes.py but not invoked in this plan — wire-up complete, callers will use them in Phase 5"

patterns-established:
  - "Session clear-then-build pattern: pop keys from session, then read session to construct ConstraintSet (cleared values become empty lists)"
  - "Transient UI feedback via Jinja2 boolean flag (lock_reset) — no JS, no redirect, no flash framework"

requirements-completed: [UI-04]

# Metrics
duration: 3min
completed: 2026-03-14
---

# Phase 4 Plan 03: Flask Session Integration Summary

**Flask cookie session wired into optimization flow: SECRET_KEY configured, lock/exclude state read from session into ConstraintSet, session cleared on upload, reset banner rendered in Jinja2, 3 integration tests green.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-14T07:31:15Z
- **Completed:** 2026-03-14T07:33:56Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- SECRET_KEY added to create_app() with OS environment variable fallback for production
- routes.py imports session from Flask and ConstraintSet from constraints module; clears session keys on file upload before building ConstraintSet; passes constraints= to optimize()
- index.html renders "Locks and excludes reset for new upload" banner only when lock_reset=True (inside show_results block)
- 3 new integration tests added: session cleared on upload, banner shown after POST, banner absent on GET

## Task Commits

Each task was committed atomically:

1. **Task 1: Add SECRET_KEY and integrate session into routes.py** - `aa7738a` (feat)
2. **Task 2 RED: Failing tests for reset banner and session clearing** - `ad9b085` (test)
3. **Task 2 GREEN: Add reset banner to index.html** - `7a00e1c` (feat)

**Plan metadata:** (docs commit — see below)

_Note: TDD task has two commits (test RED then feat GREEN)._

## Files Created/Modified

- `gbgolf/web/__init__.py` — Added SECRET_KEY config with os.environ.get() fallback
- `gbgolf/web/routes.py` — Added session import, ConstraintSet import, session clear block, ConstraintSet build, updated optimize() call with constraints=, lock_reset in render_template
- `gbgolf/web/templates/index.html` — Added reset banner div inside show_results block, conditional on lock_reset
- `tests/test_web.py` — Added test_session_cleared_on_upload, test_reset_banner_shown, test_no_reset_banner_on_get

## Decisions Made

- Session clear is unconditional on file upload — no hash comparison needed at this stage
- Session clear happens before ConstraintSet build so the new ConstraintSet always reflects cleared state (order: clear -> build -> optimize)
- check_conflicts and check_feasibility are imported but not invoked in this plan — wire-up is complete, active use deferred to Phase 5 when the lock/exclude UI is built

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 4 (Constraint Foundation) is now complete: ConstraintSet dataclass (Plan 01), ILP engine integration (Plan 02), and Flask session wire-up (Plan 03) are all done
- Phase 5 can build lock/exclude UI using session keys that are now readable and writable from routes
- The optimize() call already passes ConstraintSet; Phase 5 only needs to add routes that write to session and link UI controls

---
*Phase: 04-constraint-foundation*
*Completed: 2026-03-14*
