---
phase: 01-data-foundation
plan: 04
subsystem: data
tags: [python, argparse, cli, pipeline, integration, tdd]

# Dependency graph
requires:
  - phase: 01-data-foundation/01-02
    provides: parse_roster_csv, parse_projections_csv, match_projections, Card/ExclusionRecord/ValidationResult dataclasses
  - phase: 01-data-foundation/01-03
    provides: apply_filters, load_contest_config, ContestConfig dataclass

provides:
  - validate_pipeline() in gbgolf/data/__init__.py — full orchestration pipeline importable by Phase 2
  - load_cards() in gbgolf/data/__init__.py — parse + enrich without filtering
  - load_config() in gbgolf/data/__init__.py — contest config wrapper
  - format_summary(), format_exclusion_report(), format_verbose() in gbgolf/data/report.py
  - CLI: python -m gbgolf.data validate roster.csv proj.csv [--config] [--verbose]

affects: [02-optimizer]

# Tech tracking
tech-stack:
  added: [argparse]
  patterns:
    - "Pure formatting functions in report.py — return strings, never print; caller handles output"
    - "CLI subparser pattern with argparse — extensible for future subcommands"
    - "validate_pipeline() pool-size guard raises ValueError before optimizer receives unusable data"

key-files:
  created:
    - gbgolf/data/report.py
  modified:
    - gbgolf/data/__init__.py
    - gbgolf/data/__main__.py
    - tests/conftest.py

key-decisions:
  - "Pool-size guard in validate_pipeline() uses min(c.roster_size for c in contests) — fails fast if no contest can be filled"
  - "format_* functions return strings (not print) — __main__.py controls all I/O; functions are pure and testable"
  - "CLI catches ValueError + FileNotFoundError and exits 1 — covers both pipeline failures and missing file paths"
  - "total_parsed = valid + excluded (not raw CSV row count) — projection_warnings are data quality notes, not missing cards"

patterns-established:
  - "Formatting layer separation: report.py is the single place for human-readable output formatting"
  - "CLI entry point delegates to validate_pipeline(); output formatting is post-pipeline concern"

requirements-completed: [UPLD-01, UPLD-02, OPT-05, OPT-07, DATA-01, DATA-02, DATA-03]

# Metrics
duration: 15min
completed: 2026-03-13
---

# Phase 1 Plan 04: Pipeline Integration and CLI Summary

**validate_pipeline() orchestrating parse->enrich->filter with argparse CLI (python -m gbgolf.data validate) and human-readable exclusion report — data layer public API complete for Phase 2**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-13T23:10:00Z
- **Completed:** 2026-03-13T23:25:00Z
- **Tasks:** 2 of 3 automated (Task 3 is human checkpoint)
- **Files modified:** 4

## Accomplishments

- validate_pipeline() wires all data layer components: parse_roster_csv -> parse_projections_csv -> match_projections -> apply_filters, raises ValueError if pool < smallest contest roster_size
- report.py provides pure formatting functions: format_summary(), format_exclusion_report(), format_verbose() — all return strings, no side effects
- CLI (python -m gbgolf.data validate) exits 0 on valid input, 1 on errors; --verbose adds card table sorted by effective value descending
- Full public API exported from gbgolf.data: validate_pipeline, load_cards, load_config, Card, ContestConfig, ExclusionRecord, ValidationResult
- All 23 tests pass GREEN

## Task Commits

Each task was committed atomically:

1. **Task 1: Pipeline wiring and report formatting (report.py, __init__.py)** - `2d1c7b7` (feat)
2. **Task 2: CLI entry point (__main__.py)** - `201b793` (feat)
3. **Task 3: Human verify CLI output** - pending checkpoint

## Files Created/Modified

- `gbgolf/data/report.py` - format_summary(), format_exclusion_report(), format_verbose() — pure string formatters
- `gbgolf/data/__init__.py` - Full public API: validate_pipeline(), load_cards(), load_config() + __all__
- `gbgolf/data/__main__.py` - argparse CLI with validate subcommand, --config, --verbose flags
- `tests/conftest.py` - Added Xander Schauffele to sample data (bug fix — sample had 4 valid cards vs min roster_size 5)

## Decisions Made

- Pool-size guard uses `min(c.roster_size for c in contests)` — fails fast if valid pool cannot fill even the smallest contest
- format_* functions return strings (not print) — __main__.py controls all I/O, keeps formatting functions pure/testable
- CLI catches both ValueError and FileNotFoundError and exits 1 with "ERROR: {message}" on stderr
- total_parsed = valid + excluded — projection_warnings are data quality notes (skipped CSV rows), not missing cards

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed sample data: 4 valid cards vs roster_size min 5**
- **Found during:** Task 1 (GREEN run of test_pipeline_valid_input)
- **Issue:** conftest SAMPLE_ROSTER_CSV had 7 players but only 4 valid after exclusions (Zero Salary Guy, Tommy Fleetwood expired, No Projection Guy). VALID_CONFIG_DICT has smallest roster_size=5. validate_pipeline() correctly raised ValueError, causing test failure
- **Fix:** Added Xander Schauffele (salary=9500, Active, expires 2026-12-31) to SAMPLE_ROSTER_CSV and his projection (67.8) to SAMPLE_PROJECTIONS_CSV — now 5 valid cards matching smallest contest requirement
- **Files modified:** tests/conftest.py
- **Verification:** test_pipeline_valid_input and test_pipeline_exclusion_counts (>= 3 excluded) both pass; full 23-test suite green
- **Committed in:** 2d1c7b7 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug in test fixture)
**Impact on plan:** The pool-size guard is correct behavior. The sample data was undersized for the test config. Auto-fix required for test correctness with no scope creep.

## Issues Encountered

None beyond the auto-fixed test fixture deviation above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 2 (optimizer) can import: `from gbgolf.data import validate_pipeline, load_cards, load_config, Card, ContestConfig`
- CLI is functional and human-readable — confirmed by CLI output showing "[expired card] Tommy Fleetwood", "[$0 salary] Zero Salary Guy", "[no projection found] No Projection Guy"
- Blockers to resolve before Phase 2 (unchanged from prior plans): Franchise/Rookie column semantics from real GameBlazers export; same-golfer-in-same-lineup rule

## Self-Check: PASSED

- gbgolf/data/report.py: FOUND
- gbgolf/data/__init__.py: FOUND (contains validate_pipeline)
- gbgolf/data/__main__.py: FOUND (full CLI implementation)
- Commit 2d1c7b7: FOUND
- Commit 201b793: FOUND

---
*Phase: 01-data-foundation*
*Completed: 2026-03-13*
