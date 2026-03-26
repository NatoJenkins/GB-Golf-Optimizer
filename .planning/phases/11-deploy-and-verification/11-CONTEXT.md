# Phase 11: Deploy and Verification - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Bring the full v1.2 feature set (PostgreSQL, cron fetcher, source selector) live on the production VPS and confirm it works end-to-end in production. No new features — this phase provisions the DB, configures env vars, updates deploy.sh to run migrations, registers the cron job, and verifies both projection sources work correctly at gameblazers.silverreyes.net/golf.

</domain>

<decisions>
## Implementation Decisions

### VPS current state
- PostgreSQL 16 is already installed and running in a Docker container (same container used by nflpredictor)
- Need to create a new `gbgolf` database and user inside the existing Docker container
- DATABASE_URL: not yet in .env on the VPS — must be added
- DATAGOLF_API_KEY: not yet in .env on the VPS — must be added
- Both env vars need to be written to `/opt/GBGolfOptimizer/.env` before the service is restarted

### Deployment procedure
- `deploy.sh` must be expanded to run `flask db upgrade` via SSH after syncing files and before restarting the service
- Migration step is idempotent (Flask-Migrate) — safe to include on every deploy
- Cron registration is a one-time manual step, NOT automated in deploy.sh — DEPLOY.md provides the exact crontab line to paste
- Updated deploy.sh order: sync files → run `flask db upgrade` → restart service

### Cron job
- Schedule: `0 13 * * 2,3` (winter EST, UTC-5) / `0 12 * * 2,3` (summer EDT, UTC-4)
- Verify VPS timezone with `timedatectl` before setting the cron entry
- Command: `cd /opt/GBGolfOptimizer && FLASK_APP=gbgolf.web:create_app .venv/bin/flask fetch-projections >> logs/fetch.log 2>&1`
- Run as the deploy user (not root)
- Registered once via `crontab -e` — DEPLOY.md documents the exact line

### Verification checklist
- Cron verification: manually run `flask fetch-projections` on the VPS (do NOT wait for Tuesday/Wednesday cron fire); confirm DB rows written + log file entry + player count ≥ 30
- Source verification: browser test only — open gameblazers.silverreyes.net/golf, verify:
  1. DataGolf source: staleness label shows correct tournament name + relative age; optimizer produces lineups
  2. CSV upload source: existing file-upload behavior still works correctly
- pg_stat_activity check: skipped — pool_pre_ping=True already configured; overkill for low-traffic personal app

### DEPLOY.md update
- Full rewrite as a single authoritative deployment guide (replaces v1.0 content)
- Use real values throughout: user=deploy, IP=193.46.198.60, path=/opt/GBGolfOptimizer
- Must cover: PostgreSQL Docker DB + user creation, .env setup (both DATABASE_URL and DATAGOLF_API_KEY), flask db upgrade, cron setup, Nginx config, Gunicorn service, and verification steps
- deploy.sh is also updated (see deployment procedure above)

### Claude's Discretion
- Exact SQL commands for creating the gbgolf DB and user in the Docker container (standard PostgreSQL createuser/createdb pattern)
- DATABASE_URL connection string format for Docker-hosted PostgreSQL (likely uses host.docker.internal or container name — researcher must confirm the nflpredictor pattern to match)
- Whether the deploy.sh flask db upgrade step needs to source the venv or use the full venv path

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Deployment artifacts
- `deploy/DEPLOY.md` — existing v1.0 guide (being fully rewritten in this phase — read to understand structure)
- `deploy/deploy.sh` — existing sync script (being updated to add flask db upgrade)
- `deploy/gbgolf.service` — systemd unit file (no changes needed for v1.2)
- `deploy/gameblazers.silverreyes.net.nginx` — Nginx config (no changes needed for v1.2)

### Cron schedule reference
- `gbgolf/fetcher.py` — module docstring contains the cron schedule, exact crontab line, and timezone notes

### Database schema
- `.planning/phases/08-database-foundation/08-CONTEXT.md` — fetches + projections table schema
- `migrations/versions/4938bf64fe7e_create_fetches_and_projections_tables.py` — Flask-Migrate migration file to apply

### Environment variables
- `.env.example` — template showing required vars (DATABASE_URL, DATAGOLF_API_KEY)

### Phase requirements being verified
- `.planning/REQUIREMENTS.md` — FETCH-01 through SRC-05 (all v1.2 requirements, all verified in this phase)

No external API specs required — DataGolf integration is complete from Phase 9.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `deploy/deploy.sh`: existing SSH-based sync script — extend with `flask db upgrade` step via SSH after file sync
- `gbgolf/fetcher.py`: `flask fetch-projections` CLI command — used as the manual verification trigger for cron behavior

### Established Patterns
- Docker-hosted PostgreSQL: same container as nflpredictor — researcher must check how nflpredictor's DATABASE_URL is formatted to match the connection pattern (host, port, container name)
- `.venv/bin/flask` is the venv-relative Flask binary used in deploy.sh context

### Integration Points
- `/opt/GBGolfOptimizer/.env` — both DATABASE_URL and DATAGOLF_API_KEY must be written here before `systemctl restart gbgolf`
- Docker PostgreSQL container — new `gbgolf` DB and user created with `docker exec` commands
- `logs/` directory — must exist on VPS for fetch.log; `os.makedirs` in fetcher handles creation, but cron needs write permission

</code_context>

<specifics>
## Specific Ideas

- PostgreSQL runs in Docker (same as nflpredictor) — not a bare-metal install; DB creation uses `docker exec` to run psql inside the container
- Cron verification is done by manually running `flask fetch-projections` — no need to wait for the scheduled run
- Browser-only verification (no curl) — sufficient for a personal-use app

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 11-deploy-and-verification*
*Context gathered: 2026-03-25*
