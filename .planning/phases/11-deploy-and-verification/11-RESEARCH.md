# Phase 11: Deploy and Verification - Research

**Researched:** 2026-03-25
**Domain:** VPS deployment, PostgreSQL Docker provisioning, cron scheduling, production verification
**Confidence:** HIGH

## Summary

Phase 11 is a deployment and verification phase -- no new application code is written. The work consists of: (1) updating `deploy.sh` to include `flask db upgrade` before service restart, (2) fully rewriting `DEPLOY.md` as an authoritative deployment guide with real values, and (3) documenting the one-time VPS provisioning steps (PostgreSQL DB/user creation in Docker, `.env` setup, cron registration). Verification is manual: run `flask fetch-projections` on the VPS, then browser-check the app.

The existing deployment infrastructure is solid. `deploy.sh` already handles tar-based file sync and service restart via SSH. The systemd service, Nginx config, and Gunicorn setup are all in place from v1.0. The only code change is adding one SSH command to `deploy.sh` (the migration step). Everything else is documentation and manual VPS commands.

**Primary recommendation:** Keep the deploy.sh change minimal (one `ssh` line for `flask db upgrade`). Put all provisioning instructions in DEPLOY.md as copy-pasteable commands. Verification is a manual checklist, not automated.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- PostgreSQL 16 runs in Docker container (same as nflpredictor) -- create `gbgolf` database and user inside existing container
- DATABASE_URL and DATAGOLF_API_KEY must be added to `/opt/GBGolfOptimizer/.env`
- `deploy.sh` expanded to run `flask db upgrade` via SSH after syncing files and before restarting service
- Updated deploy.sh order: sync files -> run `flask db upgrade` -> restart service
- Cron registration is a one-time manual step, NOT automated in deploy.sh -- DEPLOY.md provides the exact crontab line
- Cron schedule: `0 13 * * 2,3` (winter EST) / `0 12 * * 2,3` (summer EDT); verify VPS timezone with `timedatectl`
- Cron command: `cd /opt/GBGolfOptimizer && FLASK_APP=gbgolf.web:create_app .venv/bin/flask fetch-projections >> logs/fetch.log 2>&1`
- Run cron as deploy user (not root)
- Cron verification: manually run `flask fetch-projections` on VPS (do NOT wait for cron fire); confirm DB rows + log entry + player count >= 30
- Source verification: browser test only -- open gameblazers.silverreyes.net/golf and verify both DataGolf and CSV sources
- pg_stat_activity check: SKIPPED -- pool_pre_ping=True already configured; overkill for low-traffic personal app
- DEPLOY.md: full rewrite as single authoritative guide with real values (user=deploy, IP=193.46.198.60, path=/opt/GBGolfOptimizer)
- DEPLOY.md must cover: PostgreSQL Docker DB + user creation, .env setup, flask db upgrade, cron setup, Nginx config, Gunicorn service, verification steps

### Claude's Discretion
- Exact SQL commands for creating the gbgolf DB and user in the Docker container
- DATABASE_URL connection string format for Docker-hosted PostgreSQL
- Whether deploy.sh flask db upgrade step needs to source the venv or use the full venv path

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

This is a verification phase -- it validates all v1.2 requirements in production rather than implementing new ones.

| ID | Description | Research Support |
|----|-------------|-----------------|
| FETCH-01 | System fetches projections from DataGolf API and writes to PostgreSQL | Verified by manually running `flask fetch-projections` on VPS; DB rows confirm write |
| FETCH-02 | Cron job triggers fetcher on Tuesday/Wednesday mornings | Cron entry documented in DEPLOY.md; manual run verifies the CLI command works |
| FETCH-03 | Fetch activity logged to file on VPS | Log file at `logs/fetch.log` checked after manual fetch run |
| FETCH-04 | Existing projections preserved on API error or low player count | Already tested in unit tests; production verification is that DB has data after a successful fetch |
| FETCH-05 | Projections stored with name, score, tournament, timestamp | DB schema applied via `flask db upgrade`; verified by inspecting fetch row after manual run |
| FETCH-06 | DataGolf names normalized to "First Last" | Already tested in unit tests; verified indirectly when optimizer matches roster names |
| SRC-01 | User can select DataGolf or CSV source | Browser verification: radio buttons visible on the page |
| SRC-02 | DataGolf source uses most recent stored projections | Browser verification: select DataGolf, run optimizer, lineups appear |
| SRC-03 | Staleness label shows tournament name and relative age | Browser verification: label visible with correct tournament name and "X days ago" |
| SRC-04 | DataGolf option disabled when no projections exist | Verified once DB has data (option becomes enabled) |
| SRC-05 | Unmatched player warnings shown for DataGolf source | Browser verification: any unmatched players appear in warning list |
</phase_requirements>

## Standard Stack

This phase introduces no new libraries. All tools are already in the project or on the VPS.

### Core (already installed)
| Tool | Version | Purpose | Notes |
|------|---------|---------|-------|
| Flask-Migrate | >= 4.1 | Schema migrations via `flask db upgrade` | Already in pyproject.toml |
| psycopg2-binary | >= 2.9 | PostgreSQL driver | Already in pyproject.toml |
| python-dotenv | >= 1.0 | Load .env vars | Already in pyproject.toml |

### VPS Infrastructure (already present)
| Tool | Version | Purpose | Notes |
|------|---------|---------|-------|
| PostgreSQL | 16 | Database server | Running in Docker container |
| Docker | (existing) | Hosts PostgreSQL container | Same container as nflpredictor |
| Nginx | (existing) | Reverse proxy | Config already deployed from v1.0 |
| Gunicorn | >= 20.0 | WSGI server | systemd service already running |
| cron | (system) | Schedule fetcher | Standard Linux cron |

### No New Dependencies
No `pip install`, no `npm install`, no new entries in pyproject.toml. The phase is purely deployment configuration and documentation.

## Architecture Patterns

### deploy.sh Update Pattern

The existing `deploy.sh` follows a simple three-step pattern:

```bash
# Step 1: Sync files via tar over SSH
tar ... | ssh "$REMOTE" "tar -xzf - -C $REMOTE_PATH"

# Step 2 (NEW): Run database migration
ssh "$REMOTE" "cd $REMOTE_PATH && .venv/bin/flask db upgrade"

# Step 3: Restart service
ssh "$REMOTE" "sudo systemctl restart gbgolf && systemctl status gbgolf --no-pager"
```

**Key decision: Use `.venv/bin/flask` directly, not `source .venv/bin/activate && flask`.**

The Flask executable installed in a venv has a shebang line pointing to the venv's Python interpreter. Running `.venv/bin/flask` directly works without activating the venv. This matches the cron command pattern already decided by the user. The existing `deploy.sh` uses `REMOTE_PATH="/opt/GBGolfOptimizer"`, so the migration command is:

```bash
ssh "$REMOTE" "cd $REMOTE_PATH && FLASK_APP=gbgolf.web:create_app .venv/bin/flask db upgrade"
```

The `FLASK_APP` env var is needed because `flask db upgrade` needs to find the app factory. The `.env` file on the VPS has `FLASK_APP=gbgolf.web:create_app`, but `ssh` commands do not source `.env` automatically. There are two options:

1. **Inline the env var** (simpler, explicit): `FLASK_APP=gbgolf.web:create_app .venv/bin/flask db upgrade`
2. **Source .env first**: `set -a && source .env && set +a && .venv/bin/flask db upgrade`

Option 1 is cleaner. However, `flask db upgrade` also needs `DATABASE_URL` to connect to PostgreSQL. So the full command must be:

```bash
ssh "$REMOTE" "cd $REMOTE_PATH && set -a && source .env && set +a && .venv/bin/flask db upgrade"
```

This sources all env vars from `.env` (DATABASE_URL, DATAGOLF_API_KEY, FLASK_APP, SECRET_KEY) before running the migration. The `set -a` / `set +a` pattern exports all sourced variables so subprocesses see them. However, since `flask db upgrade` is NOT a subprocess (it runs in the same shell), a simpler approach also works:

```bash
ssh "$REMOTE" "cd $REMOTE_PATH && source .env && .venv/bin/flask db upgrade"
```

But `source .env` without `export` means variables are set but not exported. Since Flask's `load_dotenv()` in `create_app()` reads `.env` directly, and the working directory is the project root, `flask db upgrade` will trigger `create_app()` which calls `load_dotenv()`. So the simplest correct command is:

```bash
ssh "$REMOTE" "cd $REMOTE_PATH && FLASK_APP=gbgolf.web:create_app .venv/bin/flask db upgrade"
```

`FLASK_APP` tells Flask which app to load. Once `create_app()` runs, `load_dotenv()` picks up `DATABASE_URL` from `.env`. This is the cleanest approach.

**Confidence: HIGH** -- verified by reading `gbgolf/web/__init__.py` line 18 (`load_dotenv()`) and confirming the app factory loads `.env` at startup.

### PostgreSQL Docker Provisioning Pattern

The PostgreSQL container is already running for nflpredictor. Creating the gbgolf database and user requires `docker exec` to run `psql` inside the container.

**Recommended commands for DEPLOY.md:**

```bash
# Find the container name
docker ps --filter "ancestor=postgres" --format "{{.Names}}"

# Create user and database (run as root or docker-group user)
docker exec -i <container_name> psql -U postgres <<'SQL'
CREATE USER gbgolf WITH PASSWORD 'CHANGEME';
CREATE DATABASE gbgolf OWNER gbgolf;
GRANT ALL PRIVILEGES ON DATABASE gbgolf TO gbgolf;
SQL
```

**DATABASE_URL format:**

Since the app runs on the host and PostgreSQL runs in Docker with port 5432 mapped to the host, the connection string uses `localhost`:

```
DATABASE_URL=postgresql://gbgolf:CHANGEME@localhost:5432/gbgolf
```

**Confidence: HIGH** -- standard Docker PostgreSQL port-mapping pattern. The app is NOT in a container, so `localhost:5432` reaches the Docker-mapped port.

**Important note for DEPLOY.md:** The actual container name must be discovered with `docker ps`. The DEPLOY.md should include the `docker ps` command and instruct the user to substitute the real name.

### Cron Setup Pattern

```bash
# Check VPS timezone first
timedatectl

# Edit crontab for the deploy user
crontab -e

# Add this line (winter EST = UTC-5):
0 13 * * 2,3 cd /opt/GBGolfOptimizer && FLASK_APP=gbgolf.web:create_app .venv/bin/flask fetch-projections >> logs/fetch.log 2>&1
```

**Why `FLASK_APP` is needed in the cron command:** Cron runs with a minimal environment -- no `.bashrc`, no `.profile`. The `FLASK_APP` env var tells Flask which app factory to use. Once the app factory runs, `load_dotenv()` reads `DATABASE_URL` and `DATAGOLF_API_KEY` from `/opt/GBGolfOptimizer/.env` (because `cd /opt/GBGolfOptimizer` sets the working directory first).

**Confidence: HIGH** -- matches the pattern already documented in `gbgolf/fetcher.py` module docstring.

### DEPLOY.md Rewrite Structure

The existing DEPLOY.md (v1.0) has placeholder-based instructions. The rewrite must:

1. Use real values throughout (no `<deploy_user>` or `/path/to/` placeholders)
2. Add PostgreSQL Docker provisioning section
3. Add `.env` setup section
4. Add `flask db upgrade` instructions
5. Add cron setup section
6. Keep the existing sections (systemd, Nginx, smoke test) but update paths
7. Add verification checklist matching CONTEXT.md decisions

Recommended section order:
1. Prerequisites (what should already be on the VPS)
2. PostgreSQL Setup (Docker DB + user creation)
3. Environment Variables (.env file)
4. Deploy Code (deploy.sh or manual rsync)
5. Database Migration (flask db upgrade)
6. Systemd Service (gbgolf.service)
7. Nginx Configuration
8. Cron Setup
9. Verification Checklist
10. Quick Reference (service commands)

### Anti-Patterns to Avoid
- **Automating cron in deploy.sh:** User explicitly decided cron is a one-time manual step. Do NOT add `crontab` commands to deploy.sh.
- **Running flask db upgrade as root:** The migration should run as the deploy user, using the deploy user's venv.
- **Hardcoding the Docker container name:** Container names can vary. DEPLOY.md should show how to discover it with `docker ps`.
- **Skipping FLASK_APP in migration/cron commands:** Without it, Flask cannot find the app factory and the command fails silently or with an import error.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Database migrations | Manual SQL DDL scripts | `flask db upgrade` (Flask-Migrate/Alembic) | Idempotent, versioned, already configured |
| Env var management | Custom config parsing | `python-dotenv` + `.env` file | Already integrated into create_app() |
| Process management | Custom start/stop scripts | systemd (gbgolf.service) | Already configured, handles restart-on-failure |
| Reverse proxy | Application-level routing | Nginx (already configured) | Already handles /golf prefix routing |
| Scheduling | In-app scheduler (APScheduler) | System cron | Explicit project decision; simpler, no daemon |

## Common Pitfalls

### Pitfall 1: Missing FLASK_APP in SSH/cron context
**What goes wrong:** `flask db upgrade` or `flask fetch-projections` fails with "Could not locate a Flask application" error.
**Why it happens:** SSH and cron execute with minimal environments. `FLASK_APP` is not automatically set.
**How to avoid:** Always prefix flask commands with `FLASK_APP=gbgolf.web:create_app` in deploy.sh and crontab entries.
**Warning signs:** "Error: Could not locate a Flask application" in logs or SSH output.

### Pitfall 2: .env file missing on VPS before first deploy
**What goes wrong:** `flask db upgrade` fails because `DATABASE_URL` resolves to `sqlite:///:memory:` (the fallback in create_app).
**Why it happens:** The `.env` file is in `.gitignore` and not synced by deploy.sh. It must be manually created on the VPS.
**How to avoid:** DEPLOY.md explicitly lists the `.env` creation step BEFORE the first deploy. The deploy.sh migration step will also fail visibly (migration against in-memory SQLite creates tables that vanish immediately).
**Warning signs:** Migration completes instantly with no visible output (SQLite in-memory is fast but ephemeral).

### Pitfall 3: PostgreSQL pg_hba.conf blocking local connections
**What goes wrong:** `psql` or the app cannot connect to PostgreSQL even though the container is running.
**Why it happens:** Docker PostgreSQL images default to trust for local connections, but if the container was customized, `pg_hba.conf` might reject password auth from the host.
**How to avoid:** The standard official postgres Docker image allows password auth from mapped ports by default. If issues occur, check `docker logs <container>` for authentication errors.
**Warning signs:** "FATAL: password authentication failed" in app logs or `journalctl -u gbgolf`.

### Pitfall 4: logs/ directory permissions for cron
**What goes wrong:** Cron's `>> logs/fetch.log` fails with permission denied.
**Why it happens:** The `logs/` directory may not exist or may be owned by a different user.
**How to avoid:** The `write_fetch_log()` function in `fetcher.py` calls `os.makedirs(log_dir, exist_ok=True)`, which creates the directory. However, if the cron command's `>> logs/fetch.log 2>&1` redirect runs before Flask creates the dir, the shell redirect fails. The `fetcher.py` code writes to the log internally, but the cron redirect `>> logs/fetch.log` is the SHELL writing stdout/stderr. These are separate writes.
**How to fix:** Create `logs/` directory as part of initial VPS setup: `mkdir -p /opt/GBGolfOptimizer/logs`. Or accept that the `>>` redirect will create the file if it doesn't exist (bash creates intermediate files but NOT directories).
**Recommendation:** Add `mkdir -p logs` to DEPLOY.md initial setup, and note that the shell redirect needs the directory to exist.

### Pitfall 5: venv path mismatch (venv vs .venv)
**What goes wrong:** Flask command not found.
**Why it happens:** The existing service file template uses `venv/bin`, but the CONTEXT.md cron command uses `.venv/bin`. The actual VPS may use either.
**How to avoid:** DEPLOY.md should use a consistent venv name. The CONTEXT.md decision uses `.venv` -- use that consistently in DEPLOY.md, deploy.sh, and crontab.
**Warning signs:** "No such file or directory: .venv/bin/flask" in logs.

### Pitfall 6: PRAGMA foreign_keys in PostgreSQL
**What goes wrong:** The `PRAGMA foreign_keys = ON` statement in `write_projections()` is a no-op on PostgreSQL (it's SQLite-specific syntax).
**Why it happens:** The code was written to support both SQLite (testing) and PostgreSQL (production). PostgreSQL always enforces foreign keys, so the PRAGMA is harmless.
**Impact:** None -- this is by design. PostgreSQL silently ignores unknown PRAGMAs when executed via `session.execute(text(...))`. Actually, PostgreSQL does NOT silently ignore PRAGMAs -- but SQLAlchemy's `text()` execution may handle it. This needs to be verified during deployment verification.
**Update after code review:** The `PRAGMA foreign_keys = ON` is executed as a raw SQL text. PostgreSQL will raise a syntax error on this. HOWEVER, reviewing the code more carefully: `session.execute(text("PRAGMA foreign_keys = ON"))` -- PostgreSQL does NOT understand PRAGMA syntax. This will cause a `ProgrammingError`. This is a **real bug** that will surface in production. The planner needs to account for this: either wrap it in a try/except or make it conditional on the database engine.

**CRITICAL FINDING:** `fetcher.py` line 94 (`session.execute(text("PRAGMA foreign_keys = ON"))`) will fail on PostgreSQL. This MUST be fixed before or during deployment. The fix is simple: wrap in `try/except` or check `session.bind.dialect.name != 'sqlite'`.

## Code Examples

### deploy.sh with migration step

```bash
#!/usr/bin/env bash
# Deploy GB Golf Optimizer to VPS
# Usage: bash deploy/deploy.sh
set -e

REMOTE="deploy@193.46.198.60"
REMOTE_PATH="/opt/GBGolfOptimizer"
LOCAL_PATH="$(cd "$(dirname "$0")/.." && pwd)"

echo "Syncing files..."
tar -czf - \
  --exclude='./.planning' \
  --exclude='./.git' \
  --exclude='./__pycache__' \
  --exclude='./**/__pycache__' \
  --exclude='./*.pyc' \
  --exclude='./**/*.pyc' \
  --exclude='./venv' \
  --exclude='./.venv' \
  --exclude='./*.sock' \
  -C "$LOCAL_PATH" . \
  | ssh "$REMOTE" "tar -xzf - -C $REMOTE_PATH"

echo "Running database migration..."
ssh "$REMOTE" "cd $REMOTE_PATH && FLASK_APP=gbgolf.web:create_app .venv/bin/flask db upgrade"

echo "Restarting service..."
ssh "$REMOTE" "sudo systemctl restart gbgolf && systemctl status gbgolf --no-pager"

echo "Done. Visit https://gameblazers.silverreyes.net/golf"
```

**Key changes from existing deploy.sh:**
1. Added migration step between sync and restart
2. Added `.venv` to tar exclude list (consistent with CONTEXT.md venv name)
3. `FLASK_APP` env var set inline for the migration command

### Docker PostgreSQL DB creation

```bash
# Discover the container name
docker ps --filter "ancestor=postgres" --format "table {{.Names}}\t{{.Status}}"

# Create database and user (substitute CONTAINER_NAME)
docker exec -i CONTAINER_NAME psql -U postgres <<'SQL'
CREATE USER gbgolf WITH PASSWORD 'your-secure-password';
CREATE DATABASE gbgolf OWNER gbgolf;
GRANT ALL PRIVILEGES ON DATABASE gbgolf TO gbgolf;
SQL

# Verify
docker exec -i CONTAINER_NAME psql -U postgres -c "\l" | grep gbgolf
```

### .env file content

```bash
# /opt/GBGolfOptimizer/.env
DATABASE_URL=postgresql://gbgolf:your-secure-password@localhost:5432/gbgolf
DATAGOLF_API_KEY=your-actual-api-key
SECRET_KEY=generate-a-random-string-here
FLASK_APP=gbgolf.web:create_app
```

### Crontab entry

```bash
# Tuesday and Wednesday at 8:00 AM Eastern (winter EST = UTC-5)
0 13 * * 2,3 cd /opt/GBGolfOptimizer && FLASK_APP=gbgolf.web:create_app .venv/bin/flask fetch-projections >> logs/fetch.log 2>&1
```

### Manual verification commands (on VPS)

```bash
# 1. Run fetch manually
cd /opt/GBGolfOptimizer
FLASK_APP=gbgolf.web:create_app .venv/bin/flask fetch-projections

# 2. Check log
cat logs/fetch.log

# 3. Check DB rows
docker exec -i CONTAINER_NAME psql -U gbgolf -d gbgolf -c "SELECT id, tournament_name, player_count, fetched_at FROM fetches ORDER BY fetched_at DESC LIMIT 5;"

# 4. Check projection count
docker exec -i CONTAINER_NAME psql -U gbgolf -d gbgolf -c "SELECT COUNT(*) FROM projections;"
```

## State of the Art

| Old Approach (v1.0) | Current Approach (v1.2) | When Changed | Impact |
|---------------------|------------------------|--------------|--------|
| SQLite (implicit, no DB) | PostgreSQL in Docker | Phase 8 | Requires DB provisioning on VPS |
| No migration tool | Flask-Migrate/Alembic | Phase 8 | deploy.sh must run `flask db upgrade` |
| Manual CSV projections only | DataGolf API + CSV dual source | Phase 9-10 | Requires DATAGOLF_API_KEY in .env |
| No scheduled tasks | Cron-based fetcher | Phase 9 | Requires crontab entry on VPS |
| DEPLOY.md with placeholders | DEPLOY.md with real values | Phase 11 | Single authoritative guide |

## Open Questions

1. **PRAGMA foreign_keys on PostgreSQL**
   - What we know: `fetcher.py` line 94 executes `PRAGMA foreign_keys = ON` which is SQLite-only syntax.
   - What's unclear: Whether PostgreSQL raises an error or silently ignores this. SQLAlchemy may catch it, or it may bubble up as a ProgrammingError.
   - Recommendation: The planner MUST include a task to fix this before deployment. Simplest fix: wrap in try/except or guard with a dialect check. This is a blocking issue for production deployment.

2. **Actual Docker container name on VPS**
   - What we know: PostgreSQL runs in Docker, same container as nflpredictor.
   - What's unclear: The exact container name.
   - Recommendation: DEPLOY.md includes `docker ps` discovery step. Not a code issue -- just a documentation detail.

3. **VPS venv directory name**
   - What we know: CONTEXT.md uses `.venv` in cron command. Existing service template uses `venv`.
   - What's unclear: Which actually exists on the VPS.
   - Recommendation: DEPLOY.md should document venv creation with `.venv` name to match cron command. If the VPS already has `venv/`, the service file and deploy.sh should be updated to `.venv` for consistency, OR vice versa. The planner should pick one and use it everywhere.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >= 8.0 |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -q` |

### Phase Requirements -> Test Map

Phase 11 is a verification phase. Requirements were implemented in Phases 8-10 and already have automated tests. The verification here is manual (on VPS), not new automated tests.

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FETCH-01 | Fetch projections from API, write to DB | unit (mocked) | `python -m pytest tests/test_fetcher.py::test_run_fetch_success -x` | Yes |
| FETCH-02 | CLI command registered and invocable | unit | `python -m pytest tests/test_fetcher.py::test_cli_command_registered -x` | Yes |
| FETCH-03 | Fetch activity logged to file | unit | `python -m pytest tests/test_fetcher.py::test_write_fetch_log_ok -x` | Yes |
| FETCH-04 | Existing data preserved on error | unit (mocked) | `python -m pytest tests/test_fetcher.py::test_run_fetch_low_count_guard -x` | Yes |
| FETCH-05 | Projections stored with correct columns | unit | `python -m pytest tests/test_fetcher.py::test_write_projections_inserts -x` | Yes |
| FETCH-06 | Name normalization | unit | `python -m pytest tests/test_fetcher.py::test_run_fetch_normalizes_names -x` | Yes |
| SRC-01 | Source selector UI | integration | `python -m pytest tests/test_web.py -x` | Yes |
| SRC-02 | DataGolf source uses stored projections | integration | `python -m pytest tests/test_web.py -x` | Yes |
| SRC-03 | Staleness label | integration | `python -m pytest tests/test_web.py -x` | Yes |
| SRC-04 | Disabled when no projections | integration | `python -m pytest tests/test_web.py -x` | Yes |
| SRC-05 | Unmatched player warnings | integration | `python -m pytest tests/test_web.py -x` | Yes |

### Additional Phase 11-Specific Validation
| Check | Type | How |
|-------|------|-----|
| deploy.sh migration step works | manual | Run `bash deploy/deploy.sh` and verify output |
| DEPLOY.md accuracy | manual | Follow guide on VPS, verify each step |
| Cron entry syntax valid | manual | `crontab -l` on VPS after registration |
| PRAGMA fix (if needed) | unit | Run existing test suite after fix; all tests must pass |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] Fix `PRAGMA foreign_keys = ON` in `fetcher.py` to be PostgreSQL-safe -- MUST be done before deployment or existing tests will break on real PostgreSQL

## Sources

### Primary (HIGH confidence)
- `deploy/deploy.sh` -- existing deployment script (read directly)
- `deploy/DEPLOY.md` -- existing v1.0 deployment guide (read directly)
- `deploy/gbgolf.service` -- systemd unit file (read directly)
- `gbgolf/web/__init__.py` -- app factory with `load_dotenv()` and Flask-Migrate setup (read directly)
- `gbgolf/fetcher.py` -- fetcher module with cron schedule documentation (read directly)
- `.env.example` -- environment variable template (read directly)
- `migrations/versions/4938bf64fe7e_*.py` -- migration file (read directly)
- `gbgolf/db.py` -- database model definitions (read directly)

### Secondary (MEDIUM confidence)
- [Docker PostgreSQL connection from host](https://www.w3resource.com/PostgreSQL/snippets/connect-postgresql-docker-outside.php) -- localhost:5432 pattern for host-to-Docker connections
- [Python venv docs](https://docs.python.org/3/library/venv.html) -- venv/bin/flask works without activation due to shebang
- [Docker PostgreSQL user/DB creation](https://gist.github.com/narate/f1077566f7f267b5b1911bcbe530cea6) -- docker exec pattern for createuser/createdb

### Tertiary (LOW confidence)
None -- all findings verified against project source code or official documentation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies; everything already in pyproject.toml
- Architecture: HIGH -- deploy.sh change is one line; DEPLOY.md is documentation
- Pitfalls: HIGH -- PRAGMA issue discovered by direct code reading; all other pitfalls from deployment experience
- PRAGMA bug: HIGH -- confirmed by reading fetcher.py line 94; PostgreSQL does not support PRAGMA syntax

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable -- deployment patterns don't change quickly)
