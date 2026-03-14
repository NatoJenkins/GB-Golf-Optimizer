---
phase: 05-serialization-and-re-optimize-route
plan: "02"
subsystem: ui
tags: [jinja2, html, flask, forms]

# Dependency graph
requires:
  - phase: 05-01
    provides: _serialize_cards/_deserialize_cards helpers and POST /reoptimize route
provides:
  - Re-Optimize form with hidden card_pool field rendered above lineup results in index.html
  - JS null-guarded overlay listener for reoptimize-form submit event
  - Hidden #card-pool-data input inside results block for belt-and-suspenders card pool access
affects: [future UI phases that extend the results section]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Jinja2 conditional guard pattern: {% if show_results and card_pool_json %} prevents UndefinedError on GET and error pages"
    - "JS null guard before addEventListener: const rf = getElementById(...); if (rf) { rf.addEventListener(...) } — handles conditional DOM elements"
    - "Use | e (HTML-entity-escape) for JSON in HTML attribute context — not | safe (XSS risk) or | tojson (double-encoding)"

key-files:
  created: []
  modified:
    - gbgolf/web/templates/index.html

key-decisions:
  - "Hidden card_pool carried in both a standalone #card-pool-data input and inside #reoptimize-form — belt-and-suspenders for future extensibility"
  - "JS null guard required because #reoptimize-form is conditionally rendered — absent on GET and error pages"

patterns-established:
  - "Conditional Jinja2 template blocks guarded on both show_results and card_pool_json to prevent UndefinedError"
  - "Null-guarded JS event listeners for conditionally-rendered DOM elements"

requirements-completed: [UI-02]

# Metrics
duration: 5min
completed: 2026-03-14
---

# Phase 5 Plan 02: Re-Optimize Form and JS Overlay Listener Summary

**Re-Optimize form with hidden card_pool field and null-guarded JS overlay listener added to index.html, completing the Phase 5 re-optimize UI flow**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-14T08:28:47Z
- **Completed:** 2026-03-14T08:31:16Z
- **Tasks:** 1 of 2 (Task 2 is a human-verify checkpoint, pending)
- **Files modified:** 1

## Accomplishments
- Added `#reoptimize-form` with hidden `card_pool` field guarded by `{% if show_results and card_pool_json %}` — renders above lineup results, absent on GET and error pages
- Added standalone `#card-pool-data` hidden input inside results block for belt-and-suspenders card pool access
- Added null-guarded JS listener that triggers the existing `loading-overlay` on re-optimize form submit
- Full pytest suite passes: 68 tests, 0 failures

## Task Commits

Each task was committed atomically:

1. **Task 1: Add hidden field and Re-Optimize form to index.html** - `0c8e46c` (feat)

**Plan metadata:** (pending — awaiting human-verify checkpoint approval)

## Files Created/Modified
- `gbgolf/web/templates/index.html` - Added Re-Optimize form, hidden card_pool input, and JS overlay listener

## Decisions Made
- Used `| e` filter (HTML-entity-escape) for the JSON value in attribute context — `| safe` would disable escaping of user data (XSS risk), `| tojson` would double-encode
- Standalone hidden `#card-pool-data` input added alongside the form's own hidden input for future extensibility

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 5 fully implemented — serialization helpers, POST /reoptimize route, and Re-Optimize UI form all complete
- Human browser verification pending (checkpoint:human-verify) to confirm overlay triggers and results reload correctly
- After checkpoint approval, project advances to Phase 6

---
*Phase: 05-serialization-and-re-optimize-route*
*Completed: 2026-03-14*
