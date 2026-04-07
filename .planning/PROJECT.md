# GB Golf Optimizer

## What This Is

A web application for optimizing GameBlazers fantasy golf lineups. Users upload their weekly roster export (CSV from GameBlazers) and either select auto-fetched DataGolf projections or upload a custom projections CSV, and the app generates optimal lineups for each available contest — prioritizing the cash contest (The Tips) first, then using remaining cards for The Intermediate Tee. Deployed live at https://gameblazers.silverreyes.net/golf/.

## Core Value

Generate the best possible cash contest lineups from the user's available player cards, maximizing expected score within salary and collection constraints.

## Requirements

### Validated

- ✓ User can upload a GameBlazers roster CSV export — v1.0
- ✓ User can upload a weekly projections CSV (player name + projected score) — v1.0
- ✓ App generates 3 optimal lineups for The Tips (6 golfers, salary $30K–$64K, collection limits) — v1.0
- ✓ App generates 2 optimal lineups for The Intermediate Tee (5 golfers, salary $20K–$52K) using cards not assigned to Tips — v1.0
- ✓ Each card locked to one lineup across all contests — v1.0
- ✓ Optimizer respects both salary floor and cap per contest — v1.0
- ✓ Optimizer respects collection constraints (Weekly/Core limits) per contest — v1.0
- ✓ Effective card value calculated as projected_score × multiplier — v1.0
- ✓ Lineups displayed in browser with player, salary, multiplier, projected value, and totals — v1.0
- ✓ Contest configuration stored in editable JSON file — v1.0
- ✓ Cards with $0 salary excluded from optimization — v1.0
- ✓ Cards past their Expires date excluded from optimization — v1.0
- ✓ Unmatched player report surfaced in UI — v1.0
- ✓ App deployed to Hostinger KVM 2 VPS at gameblazers.silverreyes.net/golf — v1.0
- ✓ User can lock a specific card or golfer into lineups; app re-optimizes with lock constraints — v1.1
- ✓ User can exclude a golfer from all lineups for a session — v1.1
- ✓ App re-optimizes with locked/excluded constraints without re-uploading CSVs — v1.1
- ✓ Lock/exclude UI in player pool table; sortable columns and active constraint count display — v1.1
- ✓ Full aesthetic redesign — GameBlazers × SilverReyes dark theme (Prompt + JetBrains Mono, orange/gold palette) — v1.1
- ✓ DataGolf API fetcher — `flask fetch-projections` CLI fetches `fantasy-projection-defaults` and writes to PostgreSQL — v1.2
- ✓ Cron scheduler — automatic Tuesday/Wednesday fetches with file-append logging — v1.2
- ✓ Projection source selector — user picks DataGolf (DB) or Upload CSV before optimizing; staleness label shown — v1.2
- ✓ Stale data display — last fetched tournament name + relative age shown regardless of currency — v1.2
- ✓ PostgreSQL database — fetches/projections tables with Flask-SQLAlchemy Core and Flask-Migrate — v1.2

### Active

- [ ] Contest configuration editor in the web UI (USBL-01)
- [ ] Lineup export — copy to clipboard or download as CSV (USBL-04)
- [ ] Exposure limits — cap how often a single golfer appears across all lineups (ADV-01)

### Backlog (future milestones)

- [ ] Card comparison view — side-by-side display of multiple cards for same player (USBL-02)
- [ ] Diversity constraints — enforce minimum player differences between lineups (ADV-02)
- [ ] Sensitivity analysis — show how lineup changes if a player's projection shifts (ADV-03)
- [ ] Manual projection refresh from UI without waiting for cron (MGMT-01)
- [ ] Fetch status dashboard — last fetch time, player count, error history (MGMT-02)
- [ ] Priority lineup allocation — user specifies how many lineups to prioritize per contest before backfill (ADV-04)
  - Tier 1: optimize user-specified priority count per contest, sequentially by contest order
  - Tier 2: backfill remaining (max_entries − priority) slots per contest with leftover cards
  - UI: input field per contest for priority count (default: max_entries, i.e., current behavior)
  - Validation: priority count cannot exceed max_entries for that contest
  - Example: contests with max entries 6/3/2 and priority 3/2/1 → 6 priority lineups first, then 5 backfill

### Out of Scope

- Scraping GameBlazers for contest data — manual config file update instead (contests change infrequently)
- Multi-source projection averaging — single DataGolf source for v1.2; averaging across sources is v2.0
- DataGolf data beyond projections — v1.2 uses `fantasy-projection-defaults` only (no strokes gained, rankings, etc.)
- User accounts / authentication — single shared app, no login required
- Mobile-native app — web app accessible from any browser
- RUC (Recycling Useless Cards) optimization — separate system
- Stacking constraints — team-sport DFS concept; irrelevant for individual-sport golf
- Overall score in optimization — GameBlazers "Overall" is for RUC card burning only

## Context

- **GameBlazers** (gameblazers.com): fantasy golf platform where users collect player cards with salaries and multipliers (1.0–1.5). Each week, users enter contests by building lineups from their card collection.
- **Roster export**: CSV with columns: Player, Positions, Team, Multiplier, Overall, Franchise, Rookie, Tradeable, Salary, Collection, Status, Expires.
- **Franchise / Rookie columns**: Boolean flags only — not collection types, no optimizer constraints needed. (Confirmed v1.0)
- **Salary $0 cards**: Indicate player not in tournament field this week — excluded from optimization.
- **Duplicate player cards**: Same player can appear multiple times with different multipliers/salaries; each card is a distinct optimizer variable, but a golfer may only appear once per lineup.
- **Two contests**: The Tips (cash, 3 entries) and The Intermediate Tee (non-cash, 2 entries).
- **Scoring**: Eagles (+8), birdies (+4), pars (-0.5), bogeys (-1), double bogeys (-3), double eagle or better (+15), birdie streaks (+3), bogey-free round (+2), hole-in-one (+5), plus finish position bonuses.
- **Projections**: DataGolf Scratch Plus API (`fantasy-projection-defaults`, PGA Tour / DraftKings / main slate) fetched automatically on Tue/Wed and stored in PostgreSQL. User can also upload a custom CSV. Source selected per optimizer session. If current-week fetch hasn't run, last fetched data is shown with a staleness label.
- **Hosting**: Hostinger KVM 2 VPS — full Linux server. Live at gameblazers.silverreyes.net/golf.
- **v1.0 shipped**: 2026-03-13. 1,407 LOC Python. 33 tests, all GREEN. App browser-verified.
- **v1.1 shipped**: 2026-03-25. Lock/exclude constraints, re-optimize route, full dark theme redesign.
- **v1.2 shipped**: 2026-03-26. 3,831 LOC Python. DataGolf auto-fetch, PostgreSQL, projection source selector. App live at https://gameblazers.silverreyes.net/golf/.

## Constraints

- **Tech Stack**: Python (Flask, PuLP, Pydantic v2) + Jinja2/HTML/CSS
- **Hosting**: Hostinger KVM 2 VPS at silverreyes.net — Gunicorn + Nginx + systemd
- **Data input**: No scraping — DataGolf API (automated cron), file uploads (roster CSV, custom projections CSV), or manual config
- **Database**: PostgreSQL — stores fetched projections; schema designed for v1.3 user accounts
- **Card locking**: Each card may only appear in exactly one lineup across all contests in a session

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Manual projections upload (CSV) | Simpler than scraping; user averages multiple sources themselves | ✓ Good |
| Contest config as editable JSON file | Contests change infrequently; scraping is fragile | ✓ Good |
| Python + PuLP for optimization | ILP handles salary/collection/uniqueness constraints cleanly; pure Python | ✓ Good |
| Cash contest optimized first | Maximize prize money; non-cash lineups use leftover cards | ✓ Good |
| Cards locked per lineup (cross-contest) | GameBlazers rule — same card cannot appear in multiple lineup entries | ✓ Good |
| One golfer per lineup | GameBlazers rule — same golfer may only appear once per lineup regardless of cards owned | ✓ Good |
| Franchise/Rookie are flags only | Confirmed with user — not collection types, no ILP constraints needed | ✓ Good |
| Pydantic at boundary only | Validate external JSON with Pydantic, return plain dataclass — avoids coupling in optimizer | ✓ Good |
| Collection limits as upper bounds only | 0 Weekly Collection cards per lineup is legal — constraints are maximums, not minimums | ✓ Good |
| Windows-safe temp file pattern | Write inside with-block, pass path after close — avoids NamedTemporaryFile locking on Windows | ✓ Good |
| SCRIPT_NAME via systemd env var | Flask/Werkzeug reads it to generate correct URLs under /golf prefix without code changes | ✓ Good |
| ProxyFix skipped in TESTING mode | Avoids Flask test client URL generation conflicts | ✓ Good |
| PostgreSQL via Flask-SQLAlchemy Core (no ORM) | Pydantic validates at boundaries; DB tables use Core Table objects directly | ✓ Good |
| httpx for DataGolf API client | Timeout as first-class param, no C deps, clean async upgrade path | ✓ Good |
| System cron + Flask CLI (not APScheduler/Celery) | Zero runtime complexity; cron is the right tool for weekly event scheduling | ✓ Good |
| Separate validate_pipeline_auto() (not modifying validate_pipeline()) | Zero risk to working CSV path; two clean entry points | ✓ Good |
| deploy.sh excludes .env from tar | Prevents local dev values from overwriting production secrets on every deploy | ✓ Good |
| Dialect guard for PRAGMA foreign_keys | SQLite tests need FK enforcement; PostgreSQL rejects PRAGMA — conditional on dialect.name | ✓ Good |
| Staleness threshold: 7 days | Stale data is never hidden; prior-week projections remain available until replaced | ✓ Good |

---
*Last updated: 2026-03-26 after v1.2 milestone*
