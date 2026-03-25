# Phase 9: DataGolf Fetcher - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a Flask CLI command (`flask fetch-projections`) that calls the DataGolf `fantasy-projection-defaults` API, normalizes player names, and upserts a batch into the `fetches` + `projections` tables. Wire a system cron job on the VPS to run this command automatically on Tuesday and Wednesday mornings. Write fetch activity to a log file. No UI changes in this phase.

Covers FETCH-01, FETCH-02, FETCH-03, FETCH-04, FETCH-06.

</domain>

<decisions>
## Implementation Decisions

### Minimum viable player count (FETCH-04)
- Threshold: **30 players** — if the API returns fewer than 30 players, treat as a failure
- On breach: log the error with full details, then **exit 0** (no cron alert noise)
- Existing projections in the DB are preserved unchanged when this guard trips

### Log file (FETCH-03)
- Location: **project-relative `logs/fetch.log`** (e.g., `/var/www/gbgolf/logs/fetch.log` on the VPS)
- Format: one line per fetch — `2026-03-25 08:01:22 UTC | OK | Masters Tournament | 89 players | fetch_id=42`
- Error line format: `2026-03-25 08:01:22 UTC | ERROR | <reason> | existing data preserved`
- Rotation: **grow indefinitely** — at ~2 fetches/week this will stay under 10 KB/year
- `logs/` must be in `.gitignore` — log files must not be committed

### Cron schedule (FETCH-02)
- Run on **Tuesday and Wednesday at 8:00 AM Eastern Time**
- VPS is UTC — cron entry: `0 13 * * 2,3` (winter ET = UTC-5) or `0 12 * * 2,3` (summer EDT = UTC-4)
- Phase 11 deployment must verify actual VPS timezone with `timedatectl` and compute the correct UTC offset
- Rationale: DataGolf typically publishes projections Tuesday morning; 8 AM gives them time to post before the fetch runs

### HTTP client (already decided)
- `httpx` for all DataGolf API calls — timeout configured as a first-class parameter
- `DATAGOLF_API_KEY` loaded from `.env` via python-dotenv

### Name normalization (already decided — FETCH-06)
- `parse_datagolf_name()` converts "Last, First" → "First Last"
- Then existing `normalize_name()` NFKD pipeline (from roster matching) is applied for consistency

### DB write pattern (already decided)
- Insert a `fetches` row first, capture the generated `fetch_id`
- Bulk-insert all `projections` rows referencing that `fetch_id`
- To replace stale data for the same tournament: DELETE from `fetches` WHERE tournament_name = X AND tour = Y (CASCADE deletes projections), then insert the fresh batch
- SQLAlchemy Core `text()` queries — no ORM

### API field discovery (flagged in ROADMAP)
- DataGolf field names are unconfirmed — make one live API call at phase start, log the full raw JSON response, and finalize the Pydantic model from the actual field names before writing any parsing code

### Claude's Discretion
- Exact Pydantic model field names (determined from live API discovery call)
- Transaction boundary — whether DELETE + INSERT is wrapped in a single DB transaction
- How `flask fetch-projections` reports success to stdout when run manually (informative summary is fine)
- Whether to create a `gbgolf/fetcher.py` module or put fetch logic in `gbgolf/web/routes.py` (fetcher.py is recommended for separation)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — FETCH-01 through FETCH-06 (full fetcher requirements)

### Project decisions
- `.planning/PROJECT.md` — Key Decisions table (httpx, no APScheduler, SQLAlchemy Core, cron strategy)
- `.planning/STATE.md` — Accumulated Context > Decisions section (name normalization pipeline, DB patterns, DATAGOLF_API_KEY)

### Database schema (from Phase 8)
- `.planning/phases/08-database-foundation/08-CONTEXT.md` — Two-table schema decisions, fetches/projections columns, cascade delete rationale
- `gbgolf/db.py` — Actual table definitions (fetches + projections)

No external API specs committed — field names must be confirmed via live discovery call.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `gbgolf/db.py`: `db`, `fetches` table, `projections` table — Phase 9 writes directly to these
- `gbgolf/web/__init__.py`: app factory with `db.init_app()` and `load_dotenv()` already wired — Flask CLI command gets the same app context
- `gbgolf/optimizer/engine.py` or `gbgolf/optimizer/`: likely contains `normalize_name()` — Phase 9 reuses this for FETCH-06
- `tests/conftest.py`: `app` and `db_session` fixtures from Phase 8 — extend for fetcher tests
- `tests/test_db.py`: SQLAlchemy Core `text()` query pattern — follow this pattern in fetcher

### Established Patterns
- Pydantic at boundary only, plain dicts/dataclasses internally — parse DataGolf JSON response with Pydantic at the HTTP boundary, pass plain Python objects to DB write logic
- `db.session.execute(text(...))` for all DB queries — no ORM methods
- `datetime.now(UTC)` for timestamps — consistent with Phase 8 test patterns
- `pytest` with SQLite in-memory fixture for unit tests; full PostgreSQL not required for CI

### Integration Points
- Flask CLI commands registered in `gbgolf/web/__init__.py` (app factory) via `@app.cli.command()`
- `DATAGOLF_API_KEY` and `DATABASE_URL` already expected in `.env` (`.env.example` committed in Phase 8)
- New `logs/` directory at project root — add to `.gitignore`
- Phase 11 will add the crontab entry — Phase 9 only provides the command and documents the cron line

</code_context>

<specifics>
## Specific Ideas

- Log format is human-readable one-liner: `2026-03-25 08:01:22 UTC | OK | Masters Tournament | 89 players | fetch_id=42` — easy to `tail -f` on the VPS
- The 30-player guard is intentionally loose: any real PGA event has 80+ players; only a near-empty API response or clear failure trips this
- Cron timing rationale: DataGolf posts Tuesday morning before the Thursday start; 8 AM ET is early enough to have data before the user runs lineups, late enough that DataGolf has had time to publish

</specifics>

<deferred>
## Deferred Ideas

- Manual projection refresh from the UI (MGMT-01) — future milestone, not v1.2
- Fetch status dashboard in UI (MGMT-02) — future milestone
- Logrotate.d entry for `logs/fetch.log` — too small to need rotation now; revisit at v2.0 if it grows

</deferred>

---

*Phase: 09-datagolf-fetcher*
*Context gathered: 2026-03-25*
