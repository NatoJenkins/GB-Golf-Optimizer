---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Automated Projection Fetching
status: completed
stopped_at: Phase 11 context gathered
last_updated: "2026-03-26T01:52:30.127Z"
last_activity: 2026-03-26 — Phase 10 complete (source selector UI + tests, visual verification approved)
progress:
  total_phases: 4
  completed_phases: 3
  total_plans: 5
  completed_plans: 5
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-25)

**Core value:** Generate the best possible cash contest lineups from the user's available player cards, maximizing expected score within salary and collection constraints.
**Current focus:** v1.2 Automated Projection Fetching — Phase 10 complete, Phase 11 next (Deploy and Verification)

## Current Position

Phase: 10 of 11 (Projection Source Selector) — third phase of v1.2
Plan: 2 of 2 (10-02 complete — source selector UI + test suite)
Status: Phase 10 complete
Last activity: 2026-03-26 — Phase 10 complete (source selector UI + tests, visual verification approved)

Progress: [##########] 100% (2/2 plans done in Phase 10)

## Accumulated Context

### Decisions

All key decisions logged in PROJECT.md Key Decisions table.

Recent decisions affecting current work:
- Database: PostgreSQL via Flask-SQLAlchemy (Core queries, no ORM) with Flask-Migrate for schema migrations
- HTTP client: httpx for DataGolf API calls (timeout as first-class param, no C deps)
- Scheduler: system cron invoking `flask fetch-projections` CLI command (no APScheduler/Celery)
- Secrets: `.env` file with python-dotenv (DATABASE_URL + DATAGOLF_API_KEY)
- Name normalization: `parse_datagolf_name()` for "Last, First" -> "First Last" + existing `normalize_name()` NFKD pipeline
- Phase 8: SQLite in-memory fallback when DATABASE_URL not set (avoids KeyError in test/dev)
- Phase 8: pool_pre_ping=True for Gunicorn forked worker safety
- Phase 8: ON DELETE CASCADE at database level for fetches->projections FK
- Phase 9: DataGolf projected points field is `proj_points_total` (confirmed via live discovery)
- Phase 9: Tournament name available as top-level `event_name` in API response
- Phase 9: API response is dict with `projections` list, not flat list
- Phase 9: SQLite reuses IDs after DELETE — tests verify by player names not IDs
- Phase 9: CLI uses @app.cli.command (no @with_appcontext needed — Flask 2.0+ provides app context automatically)
- Phase 9: Cron schedule documented as module docstring in fetcher.py for Phase 11 deployment reference
- Phase 10: Separate validate_pipeline_auto() function instead of modifying existing validate_pipeline() -- zero risk to CSV path
- Phase 10: _db_template_vars() helper injected in every render_template call -- prevents missing DB context on error paths
- Phase 10: Staleness threshold: 7 days (is_stale flag in _get_latest_fetch)
- Phase 10: Conditional required attribute on projections file input -- only required when CSV source active
- Phase 10: Hidden input projection_source synced by JS from radio buttons for reliable form submission

### Pending Todos

None.

### Blockers/Concerns

None — DataGolf API field names confirmed, API key working.

## Performance Metrics

| Phase | Plan | Duration | Tasks | Files |
|-------|------|----------|-------|-------|
| 08 | 01 | 6min | 3 | 8 |
| 09 | 01 | 4min | 2 | 5 |
| 09 | 02 | 3min | 2 | 3 |
| 10 | 01 | 3min | 2 | 3 |
| 10 | 02 | 4min | 2 | 4 |

## Session Continuity

Last session: 2026-03-26T01:52:30.124Z
Stopped at: Phase 11 context gathered
Resume file: .planning/phases/11-deploy-and-verification/11-CONTEXT.md
