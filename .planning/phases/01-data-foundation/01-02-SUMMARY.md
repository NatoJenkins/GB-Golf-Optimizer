---
phase: 01-data-foundation
plan: 02
subsystem: data
tags: [python, dataclasses, csv-parsing, unicode-normalization, python-dateutil, tdd]

# Dependency graph
requires:
  - phase: 01-data-foundation/01-01
    provides: pyproject.toml, gbgolf.data package skeleton, TDD-RED test stubs for roster/projections/matching
provides:
  - Card, ExclusionRecord, ValidationResult dataclasses in gbgolf/data/models.py
  - parse_roster_csv() in gbgolf/data/roster.py — reads GameBlazers CSV, returns list[Card]
  - parse_projections_csv() in gbgolf/data/projections.py — returns (dict[str,float], list[str])
  - normalize_name() in gbgolf/data/matching.py — NFKD accent decomposition
  - match_projections() in gbgolf/data/matching.py — enriches cards with effective_value
affects: [01-03, 01-04, 02-optimizer]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "NFKD Unicode normalization for golfer name matching (Åberg == Aberg)"
    - "Tuple return (dict, warnings) for CSV parsers — callers decide how to handle skipped rows"
    - "dateutil.parser as fallback after date.fromisoformat for Expires column flexibility"

key-files:
  created:
    - gbgolf/data/models.py
    - gbgolf/data/roster.py
    - gbgolf/data/projections.py
    - gbgolf/data/matching.py
  modified:
    - tests/test_projections.py

key-decisions:
  - "parse_roster_csv validates required columns immediately after DictReader open — fails fast with sorted missing column list"
  - "effective_value = round(projected_score * multiplier, 4) to avoid float precision noise"
  - "dateutil fallback on Expires: unparseable = None (include card) — safer than silently excluding"
  - "projections.py score column lookup is flexible (projected_score/score/projection) and name column lookup is flexible (player/name/golfer)"

patterns-established:
  - "Roster columns validated against REQUIRED_ROSTER_COLUMNS set before any row is read"
  - "Normalize-then-lookup pattern: normalize_name() called on both sides at match time"
  - "Warnings-as-return-value pattern: callers receive skipped-row context without exceptions"

requirements-completed: [UPLD-01, UPLD-02, OPT-05, DATA-02]

# Metrics
duration: 6min
completed: 2026-03-13
---

# Phase 1 Plan 02: Data Models + CSV Parsers Summary

**Card dataclass + parse_roster_csv/parse_projections_csv/match_projections with NFKD accent normalization, enabling Åberg-to-Aberg matching and effective_value calculation across all 11 tests GREEN**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-13T22:50:33Z
- **Completed:** 2026-03-13T22:56:38Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Card, ExclusionRecord, ValidationResult dataclasses — single source of truth for card data, asdict()-serializable
- parse_roster_csv() validates required columns upfront, parses salary as int(float()) for "0.00" format, uses dateutil fallback for Expires
- parse_projections_csv() returns (dict[str,float], list[str]) with flexible column detection; skips bad rows with warning strings
- normalize_name() via NFKD decomposition confirms normalize_name("Ludvig Åberg") == normalize_name("Ludvig Aberg")
- match_projections() sets effective_value = projected_score * multiplier on matched cards; unmatched cards left as None

## Task Commits

Each task was committed atomically:

1. **Task 1: Data models (models.py)** - `7274038` (feat)
2. **Task 2: Roster + projections parsers (roster.py, projections.py, matching.py)** - `d8b7d45` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `gbgolf/data/models.py` - Card, ExclusionRecord, ValidationResult dataclasses with optional projected_score/effective_value fields
- `gbgolf/data/matching.py` - normalize_name() NFKD decomposition; match_projections() enriches Card list from projections dict
- `gbgolf/data/roster.py` - parse_roster_csv() with column validation, salary/multiplier/expires parsing
- `gbgolf/data/projections.py` - parse_projections_csv() returning (dict, warnings) with flexible column detection
- `tests/test_projections.py` - Fixed first test stub: added missing tuple unpack (Rule 1 bug auto-fix)

## Decisions Made

- `effective_value = round(..., 4)`: avoids float precision noise without sacrificing meaningful precision for optimizer ranking
- dateutil fallback for Expires treats unparseable dates as None (card included) — conservative default, safer than accidental exclusion
- Flexible column detection in projections parser (projected_score/score/projection, player/name/golfer) accommodates real-world projection source variation

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_projections.py first stub missing tuple unpack**
- **Found during:** Task 2 (parsers implementation)
- **Issue:** `test_valid_projections_returns_dict` called `result = parse_projections_csv(path)` then `assert isinstance(result, dict)` — function correctly returns a tuple, making the assertion fail on a working implementation
- **Fix:** Changed to `result, warnings = parse_projections_csv(path)` to match the interface contract confirmed by the other two tests in the same file
- **Files modified:** tests/test_projections.py
- **Verification:** All 11 tests pass GREEN after fix
- **Committed in:** d8b7d45 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug in test stub)
**Impact on plan:** Auto-fix required for test correctness. No scope creep; the interface contract was already established by the other two tests.

## Issues Encountered

None beyond the one auto-fixed test stub deviation above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All Plan 02 success criteria met: Card is single source of truth, ValueError on missing columns, (dict, warnings) tuple from projections parser, Unicode normalization works, effective_value calculated correctly
- Plans 03 (filters) and 04 (config/pipeline) have test stubs waiting — they import from gbgolf.data.filters and gbgolf.data.config which remain unimplemented
- Blockers noted in STATE.md still open: Franchise/Rookie column semantics and same-golfer lineup rule need clarification before Phase 2

---
*Phase: 01-data-foundation*
*Completed: 2026-03-13*
