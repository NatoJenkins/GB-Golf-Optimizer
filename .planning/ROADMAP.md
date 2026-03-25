# Roadmap: GB Golf Optimizer

## Milestones

- ✅ **v1.0 MVP** — Phases 1-3 (shipped 2026-03-13)
- ✅ **v1.1 Manual Lock/Exclude** — Phases 4-7 (shipped 2026-03-25)
- 🚧 **v1.2 Automated Projection Fetching** — Phases 8-11 (in progress)

## Phases

<details>
<summary>v1.0 MVP (Phases 1-3) — SHIPPED 2026-03-13</summary>

- [x] Phase 1: Data Foundation (4/4 plans) — completed 2026-03-13
- [x] Phase 2: Optimization Engine (3/3 plans) — completed 2026-03-13
- [x] Phase 3: Web Application and Deployment (3/3 plans) — completed 2026-03-13

See: `.planning/milestones/v1.0-ROADMAP.md` for full phase details.

</details>

<details>
<summary>v1.1 Manual Lock/Exclude (Phases 4-7) — SHIPPED 2026-03-25</summary>

- [x] Phase 4: Constraint Foundation (3/3 plans) — completed 2026-03-14
- [x] Phase 5: Serialization and Re-Optimize Route (2/2 plans) — completed 2026-03-14
- [x] Phase 6: Lock/Exclude UI (3/3 plans) — completed 2026-03-14
- [x] Phase 7: Polish (2/2 plans) — completed 2026-03-14

</details>

### 🚧 v1.2 Automated Projection Fetching (In Progress)

**Milestone Goal:** Automatically fetch DFS golf projections from the DataGolf API on a schedule and store them in PostgreSQL, letting users choose between DataGolf projections or a manually uploaded CSV before optimizing.

- [x] **Phase 8: Database Foundation** — PostgreSQL setup, Flask-SQLAlchemy integration, projections table schema
- [ ] **Phase 9: DataGolf Fetcher** — API client, name normalization, transactional upsert, cron scheduling, fetch logging
- [ ] **Phase 10: Projection Source Selector** — UI source picker, DB projection loading, staleness display, empty-state handling, unmatched warnings
- [ ] **Phase 11: Deploy and Verification** — Production deployment of PostgreSQL + cron + source selector, end-to-end verification on VPS

## Phase Details

### Phase 8: Database Foundation
**Goal**: The Flask app connects to PostgreSQL and has a projections table ready for the fetcher to write to
**Depends on**: Phase 7 (v1.1 complete)
**Requirements**: FETCH-05
**Success Criteria** (what must be TRUE):
  1. Flask app starts cleanly with a PostgreSQL connection configured via DATABASE_URL environment variable
  2. A `projections` table exists with columns for player name, projected score, tournament name, and fetch timestamp
  3. The database connection works correctly with Gunicorn's forked worker model (each worker gets its own connection pool)
  4. DATABASE_URL and DATAGOLF_API_KEY are loaded from a `.env` file that is not committed to version control
**Plans:** 1 plan
Plans:
- [x] 08-01-PLAN.md — Dependencies, db.py table definitions, app factory wiring, Flask-Migrate init, DB tests

### Phase 9: DataGolf Fetcher
**Goal**: The system automatically fetches projections from the DataGolf API and stores them safely in the database on a cron schedule
**Depends on**: Phase 8
**Requirements**: FETCH-01, FETCH-02, FETCH-03, FETCH-04, FETCH-06
**Success Criteria** (what must be TRUE):
  1. Running `flask fetch-projections` retrieves player projections from the DataGolf `fantasy-projection-defaults` endpoint and writes them to the projections table
  2. DataGolf player names in "Last, First" format are normalized to "First Last" before storage, matching GameBlazers roster name format
  3. If the API returns an error or fewer than a minimum viable player count, existing stored projections are preserved (not deleted or overwritten)
  4. A cron job on the VPS triggers the fetcher automatically on Tuesday and Wednesday mornings, with fetch activity (player count, tournament name, timestamp, errors) written to a log file
  5. Running the fetcher multiple times for the same event is idempotent — it replaces stale data cleanly without duplicating rows
**Plans:** 2 plans
Plans:
- [ ] 09-01-PLAN.md — httpx dependency, API discovery call, fetcher module (Pydantic model, name normalization, DB writes, fetch orchestration, logging), comprehensive test suite
- [ ] 09-02-PLAN.md — Flask CLI command wiring, cron documentation, live end-to-end fetch verification

### Phase 10: Projection Source Selector
**Goal**: Users can choose between DataGolf projections from the database or a manually uploaded CSV before running the optimizer
**Depends on**: Phase 9
**Requirements**: SRC-01, SRC-02, SRC-03, SRC-04, SRC-05
**Success Criteria** (what must be TRUE):
  1. User sees a "DataGolf" / "Upload CSV" source selector on the optimizer page and can choose either before optimizing
  2. When "DataGolf" is selected, the optimizer uses the most recently stored projections from the database and produces lineups identically to the CSV path
  3. The UI displays the stored tournament name and relative fetch age (e.g., "Arnold Palmer Invitational -- fetched 3 days ago") when DataGolf is selected
  4. If no projections have ever been fetched, the DataGolf option is disabled with a "No projections available yet" message
  5. When DataGolf projections are used, unmatched player warnings appear for roster players not found in the stored projections (same report format as CSV source)
**Plans**: TBD

### Phase 11: Deploy and Verification
**Goal**: The full v1.2 feature set (PostgreSQL, cron fetcher, source selector) is deployed and verified working end-to-end on the production VPS
**Depends on**: Phase 10
**Requirements**: (verification phase — validates FETCH-01 through SRC-05 in production environment)
**Success Criteria** (what must be TRUE):
  1. Cron job fires on schedule on the VPS and the fetch log file shows successful fetches with player count and tournament name
  2. Both projection sources (DataGolf and CSV upload) produce correct optimizer results in the deployed app at gameblazers.silverreyes.net/golf
  3. PostgreSQL connection pool stays bounded under normal use (verified via `pg_stat_activity`)
  4. Staleness label displays correct tournament name and relative age for both current-week and prior-week projection states
**Plans**: TBD

## Progress

**Execution Order:** Phases 8 -> 9 -> 10 -> 11

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Data Foundation | v1.0 | 4/4 | Complete | 2026-03-13 |
| 2. Optimization Engine | v1.0 | 3/3 | Complete | 2026-03-13 |
| 3. Web Application and Deployment | v1.0 | 3/3 | Complete | 2026-03-13 |
| 4. Constraint Foundation | v1.1 | 3/3 | Complete | 2026-03-14 |
| 5. Serialization and Re-Optimize Route | v1.1 | 2/2 | Complete | 2026-03-14 |
| 6. Lock/Exclude UI | v1.1 | 3/3 | Complete | 2026-03-14 |
| 7. Polish | v1.1 | 2/2 | Complete | 2026-03-14 |
| 8. Database Foundation | v1.2 | 1/1 | Complete | 2026-03-25 |
| 9. DataGolf Fetcher | v1.2 | 0/2 | Planned | - |
| 10. Projection Source Selector | v1.2 | 0/? | Not started | - |
| 11. Deploy and Verification | v1.2 | 0/? | Not started | - |

---
*Roadmap created: 2026-03-13*
*Last updated: 2026-03-25 after Phase 9 planning complete (2 plans)*
