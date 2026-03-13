---
phase: 01-data-foundation
plan: 03
subsystem: data
tags: [pydantic, dataclasses, filters, config, json]

# Dependency graph
requires:
  - phase: 01-data-foundation plan 01
    provides: Card and ExclusionRecord dataclasses from gbgolf.data.models

provides:
  - apply_filters() in gbgolf/data/filters.py — three exclusion rules with exact reason strings
  - load_contest_config() in gbgolf/data/config.py — Pydantic v2 validated config loader
  - ContestConfig dataclass for internal contest parameter representation
  - contest_config.json at project root with The Tips and The Intermediate Tee defaults

affects: [02-optimizer, optimizer phase ILP formulation, lineup builder]

# Tech tracking
tech-stack:
  added: [pydantic v2 model_validator, dataclasses]
  patterns: [Pydantic-at-boundary pattern — validate at I/O, use plain dataclasses internally]

key-files:
  created:
    - gbgolf/data/filters.py
    - gbgolf/data/config.py
    - contest_config.json
  modified: []

key-decisions:
  - "Pydantic used only at config file boundary; ContestConfig is a plain dataclass internally — avoids Pydantic coupling across the codebase"
  - "model_validator (mode='after') used for cross-field salary_max > salary_min constraint — field_validator cannot access sibling fields in all cases"
  - "Filter order: salary == 0 checked first, then expired, then no projection — first matching rule wins, no duplicate ExclusionRecords per card"
  - "expires < today (strict less-than) so cards expiring today remain valid — matches plan spec"

patterns-established:
  - "Pydantic-at-boundary: validate external JSON with Pydantic model, return plain dataclass — keeps optimizer code free of Pydantic coupling"
  - "Exclusion filter: single-pass loop over cards, first-match-wins, appends to excluded list"

requirements-completed: [OPT-07, DATA-01, DATA-02, DATA-03]

# Metrics
duration: 8min
completed: 2026-03-13
---

# Phase 1 Plan 03: Exclusion Filters and Contest Config Loader Summary

**Pydantic-validated contest config loader and three-rule card exclusion filter ($0 salary / expired / no projection) with exact reason strings**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-13T23:00:00Z
- **Completed:** 2026-03-13T23:08:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- apply_filters() applies all three exclusion rules in priority order; a single card produces at most one ExclusionRecord; cards expiring today are valid
- load_contest_config() loads and validates contest JSON via Pydantic v2 at the boundary and returns plain ContestConfig dataclasses
- contest_config.json provides default contest definitions for The Tips (6-player, $30k-$64k) and The Intermediate Tee (5-player, $20k-$52k)

## Task Commits

Each task was committed atomically:

1. **Task 1: Exclusion filters (filters.py)** - `17bf064` (feat)
2. **Task 2: Contest config loader (config.py + contest_config.json)** - `160bf5d` (feat)

## Files Created/Modified

- `gbgolf/data/filters.py` - apply_filters() with $0 salary / expired / no projection exclusion rules
- `gbgolf/data/config.py` - load_contest_config(), ContestConfig dataclass, _ContestConfigModel Pydantic validator
- `contest_config.json` - Default contest config at project root with The Tips and The Intermediate Tee

## Decisions Made

- Pydantic used only at config file boundary; ContestConfig is a plain dataclass internally — avoids Pydantic coupling across the codebase
- model_validator (mode="after") used for cross-field salary_max > salary_min constraint
- Filter order: salary == 0 first, then expired card, then no projection — first match wins

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Data foundation complete: models, CSV parsers, name matching, exclusion filters, and contest config all implemented and tested
- Phase 2 (optimizer) can import apply_filters, load_contest_config, and ContestConfig directly
- Blockers to resolve before Phase 2: confirm Franchise/Rookie column semantics from a real GameBlazers export; confirm same-golfer-in-same-lineup rule

---
*Phase: 01-data-foundation*
*Completed: 2026-03-13*
