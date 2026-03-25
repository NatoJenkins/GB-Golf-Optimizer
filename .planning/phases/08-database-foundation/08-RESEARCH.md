# Phase 8: Database Foundation - Research

**Researched:** 2026-03-25
**Domain:** Flask-SQLAlchemy Core + Flask-Migrate + PostgreSQL connection management
**Confidence:** HIGH

## Summary

Phase 8 wires PostgreSQL into the existing Flask app factory. The work is purely infrastructure: define two tables (`fetches` and `projections`) using SQLAlchemy Core `Table` objects (no ORM), configure Flask-Migrate for schema migrations, and load secrets from a `.env` file via python-dotenv. No data fetching, no UI changes.

The stack is well-established and heavily documented. Flask-SQLAlchemy 3.1.x supports Core-style `db.Table` definitions natively with automatic metadata binding. Flask-Migrate wraps Alembic and integrates cleanly with the app factory pattern via `init_app`. The main technical risk is connection pooling with Gunicorn's pre-fork worker model, which is solved by `pool_pre_ping=True` and ensuring the engine is created inside the app factory (not at module level) -- both are already the default pattern when using Flask-SQLAlchemy properly.

**Primary recommendation:** Use `gbgolf/db.py` as the single module for `db = SQLAlchemy()` and both `Table` definitions. Wire into the app factory with `db.init_app(app)` and `Migrate(app, db)`. Use `pool_pre_ping=True` in `SQLALCHEMY_ENGINE_OPTIONS` to handle stale connections under Gunicorn. Use SQLite in-memory for test fixtures.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Two-table design: `fetches` table (id, tournament_name, fetched_at, player_count, source, tour) and `projections` table (id, fetch_id FK, player_name, projected_score)
- Flask-SQLAlchemy Core (no ORM) -- tables declared as `sqlalchemy.Table` objects, queries via `db.session.execute(text(...))`
- Flask-Migrate for schema migrations -- migration scripts committed to version control
- python-dotenv for `.env` secrets -- `DATABASE_URL` and `DATAGOLF_API_KEY`
- No APScheduler/Celery -- system cron calls `flask fetch-projections` CLI
- `projected_score` uses REAL/FLOAT type (PuLP converts to float anyway)
- `source` column hardcoded `'datagolf'` for v1.2; `tour` column hardcoded `'pga'` for v1.2
- `fetched_at` always inserted as UTC via `datetime.now(UTC)`

### Claude's Discretion
- Where `db = SQLAlchemy()` lives (recommended: `gbgolf/db.py`)
- Exact migration script structure and Flask-Migrate init location
- ON DELETE CASCADE vs application-level delete ordering
- `.env.example` contents and wording
- Connection pool sizing for Gunicorn forked workers (NullPool vs pre-ping approach)
- Test setup for DB integration

### Deferred Ideas (OUT OF SCOPE)
- Module organization beyond `db.py` -- not discussed further
- v1.3 `user_id` column -- explicitly deferred to a future Flask-Migrate migration
- Testing approach details -- left to Claude's discretion

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FETCH-05 | Fetched projections are stored with player name, projected score, tournament name, and fetch timestamp per record | Two-table schema (fetches + projections) captures all four fields: `player_name` and `projected_score` on projections; `tournament_name` and `fetched_at` on fetches (linked via `fetch_id` FK). Table definitions and migration setup documented in Architecture Patterns and Code Examples sections. |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flask-SQLAlchemy | 3.1.1 | SQLAlchemy integration for Flask (db object, session management, config binding) | Official Pallets-eco extension; handles app context, session scoping, engine configuration via Flask config keys |
| Flask-Migrate | 4.1.0 | Alembic wrapper for Flask -- schema migration CLI (`flask db init/migrate/upgrade`) | Miguel Grinberg's standard; only maintained Flask migration tool; auto-detects Table changes |
| SQLAlchemy | 2.0.48 | Database toolkit -- Core Table definitions, text() queries, connection pooling | Already a transitive dependency of Flask-SQLAlchemy; pinning ensures compatibility |
| psycopg2-binary | 2.9.11 | PostgreSQL database adapter for Python | Most widely used PostgreSQL driver; `-binary` avoids C compiler requirement on deployment |
| python-dotenv | 1.2.2 | Load `.env` file into `os.environ` | 12-factor app pattern; Flask docs recommend it; no code coupling to secrets |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Alembic | (transitive) | Migration engine underlying Flask-Migrate | Installed automatically; never imported directly in app code |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| psycopg2-binary | psycopg[binary] (psycopg3) | psycopg3 is async-native, but Flask-SQLAlchemy sync session uses psycopg2 by default; psycopg2-binary is the established choice and avoids driver confusion |
| NullPool | QueuePool + pool_pre_ping | NullPool opens/closes a connection per query (slow); QueuePool with `pool_pre_ping=True` validates connections on checkout -- better performance, safe for forked workers when engine is created inside app factory |

**Installation:**
```bash
pip install flask-sqlalchemy==3.1.1 flask-migrate==4.1.0 psycopg2-binary==2.9.11 python-dotenv==1.2.2
```

**Version verification:** Versions confirmed via PyPI as of 2026-03-25.

## Architecture Patterns

### Recommended Project Structure
```
gbgolf/
  __init__.py          # app factory (unchanged except db init)
  db.py                # NEW: db = SQLAlchemy(), Table definitions
  data/                # existing data layer
  optimizer/           # existing optimizer
  web/
    __init__.py        # create_app() -- add db.init_app, Migrate
    routes.py          # existing routes (unchanged)
migrations/            # NEW: Flask-Migrate auto-generated (committed to VCS)
.env                   # NEW: DATABASE_URL, DATAGOLF_API_KEY (git-ignored)
.env.example           # NEW: template with placeholder values (committed)
.gitignore             # NEW: add .env exclusion
```

### Pattern 1: db.py Module (Core Table Definitions)

**What:** Single module that creates the `SQLAlchemy()` instance and defines both tables using `db.Table`. Importing `db` from this module avoids circular imports between the app factory and any future blueprints that need DB access.

**When to use:** Always -- this is the canonical Flask-SQLAlchemy pattern for separating the extension instance from the app factory.

**Example:**
```python
# gbgolf/db.py
import sqlalchemy as sa
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

fetches = db.Table(
    "fetches",
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("tournament_name", sa.String, nullable=False),
    sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("player_count", sa.Integer, nullable=False),
    sa.Column("source", sa.String, nullable=False),
    sa.Column("tour", sa.String, nullable=False),
)

projections = db.Table(
    "projections",
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("fetch_id", sa.Integer, sa.ForeignKey("fetches.id", ondelete="CASCADE"), nullable=False),
    sa.Column("player_name", sa.String, nullable=False),
    sa.Column("projected_score", sa.Float, nullable=False),
)
```
Source: [Flask-SQLAlchemy Models and Tables docs](https://flask-sqlalchemy.readthedocs.io/en/stable/models/), [SQLAlchemy 2.0 MetaData docs](https://docs.sqlalchemy.org/en/20/core/metadata.html)

### Pattern 2: App Factory Integration

**What:** Wire `db.init_app(app)` and `Migrate(app, db)` into the existing `create_app()` function. Load `.env` before reading config values.

**When to use:** Always -- this is the Flask extension initialization pattern.

**Example:**
```python
# gbgolf/web/__init__.py (modified create_app)
import os
from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from gbgolf.db import db

def create_app() -> Flask:
    load_dotenv()  # loads .env into os.environ

    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Database config
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
    }

    # ... existing config (SECRET_KEY, CONFIG_PATH, etc.) ...

    db.init_app(app)
    Migrate(app, db)

    # ... existing blueprint registration ...
    return app
```
Source: [Flask-Migrate docs](https://flask-migrate.readthedocs.io/), [Flask-SQLAlchemy Configuration](https://flask-sqlalchemy.readthedocs.io/en/stable/config/)

### Pattern 3: Migration Workflow

**What:** Flask-Migrate CLI commands to initialize and generate the first migration.

**When to use:** Once during Phase 8 setup, then each time schema changes.

**Commands:**
```bash
# One-time: create migrations/ directory structure
flask db init

# Generate migration script from Table definitions
flask db migrate -m "create fetches and projections tables"

# Apply migration to database
flask db upgrade
```

**Important:** The `flask db migrate` auto-detection works with `db.Table` definitions because Flask-SQLAlchemy registers them on `db.metadata`. However, Alembic cannot detect table renames, column renames, or anonymous constraint changes -- always review generated scripts.

### Pattern 4: ON DELETE CASCADE at Database Level

**What:** Use `ondelete="CASCADE"` on the `ForeignKey` definition so PostgreSQL automatically deletes child `projections` rows when a parent `fetches` row is deleted.

**Why over application-level:** Database-level cascade is atomic, faster, and works even if deletion happens outside the application (e.g., manual SQL). Since we use Core (no ORM relationships), there is no ORM-level cascade option anyway -- database-level is the only choice.

Source: [SQLAlchemy Cascade docs](https://docs.sqlalchemy.org/en/20/orm/cascades.html)

### Anti-Patterns to Avoid
- **Defining `db = SQLAlchemy(app)` inside the app factory:** Creates a new extension per call. Define `db` at module level and use `db.init_app(app)` instead.
- **Importing `db` from the app factory module:** Causes circular imports when routes/CLI commands need DB access. Keep `db` in its own module (`gbgolf/db.py`).
- **Using `db.create_all()` instead of Flask-Migrate:** Loses migration history. `db.create_all()` is only appropriate for ephemeral test databases.
- **Sharing database connections across forked workers:** Never create the engine at module level before forking. Flask-SQLAlchemy's `init_app` pattern already prevents this.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Schema migrations | Raw SQL `CREATE TABLE` scripts | Flask-Migrate (`flask db migrate/upgrade`) | Tracks schema versions, generates diffs, reversible, team-friendly |
| Connection pooling | Manual connection open/close | SQLAlchemy QueuePool (default) + `pool_pre_ping` | Handles stale connections, connection limits, thread safety |
| Environment variable loading | `os.environ` with manual file parsing | python-dotenv `load_dotenv()` | Handles comments, multiline values, doesn't override existing env vars |
| Table metadata registration | Manual `MetaData()` objects | `db.Table()` (Flask-SQLAlchemy auto-binds metadata) | Automatically connects to the right engine, no manual metadata tracking |

**Key insight:** Flask-SQLAlchemy + Flask-Migrate together handle the entire lifecycle from table definition through migration generation, schema application, and runtime connection management. Each piece is under 5 lines of integration code.

## Common Pitfalls

### Pitfall 1: Forgetting to Import Table Definitions Before `flask db migrate`
**What goes wrong:** Flask-Migrate/Alembic sees an empty metadata and generates an empty migration script.
**Why it happens:** `db.Table` calls register on `db.metadata` at import time. If `gbgolf/db.py` is never imported before `flask db migrate` runs, the tables don't exist in metadata.
**How to avoid:** Import `db` (and by extension the Table definitions) in the app factory. The `from gbgolf.db import db` in `create_app()` ensures tables are registered.
**Warning signs:** Migration script has empty `upgrade()` and `downgrade()` functions.

### Pitfall 2: SQLALCHEMY_DATABASE_URI vs DATABASE_URL Naming
**What goes wrong:** Flask-SQLAlchemy expects `SQLALCHEMY_DATABASE_URI` as its config key. The `.env` file stores `DATABASE_URL` (Heroku/Railway convention). If you set `app.config["DATABASE_URL"]` instead of `app.config["SQLALCHEMY_DATABASE_URI"]`, the extension silently uses SQLite.
**Why it happens:** Name mismatch between deployment convention and Flask-SQLAlchemy expectation.
**How to avoid:** Explicitly map: `app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]`
**Warning signs:** App starts but queries fail with "no such table" (SQLite fallback).

### Pitfall 3: PostgreSQL URL Scheme `postgres://` vs `postgresql://`
**What goes wrong:** SQLAlchemy 2.x requires `postgresql://` scheme. Some hosting providers (Heroku legacy) provide `postgres://` which causes a deprecation warning or connection failure.
**Why it happens:** SQLAlchemy tightened URL parsing in 2.0.
**How to avoid:** Either ensure `DATABASE_URL` uses `postgresql://`, or add a one-liner fixup: `url = os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1)`
**Warning signs:** `sqlalchemy.exc.ArgumentError` about invalid URL scheme.

### Pitfall 4: Gunicorn Pre-fork Connection Sharing
**What goes wrong:** If the app creates DB connections before Gunicorn forks workers, those TCP connections get shared across processes, causing random query failures and data corruption.
**Why it happens:** Gunicorn's `--preload` flag (or importing the app at module level) creates the engine before fork.
**How to avoid:** Flask-SQLAlchemy's `init_app` pattern naturally creates the engine lazily (on first request), which happens inside each worker. Don't use `--preload` with DB apps, or if you must, call `db.engine.dispose()` in a `post_fork` hook.
**Warning signs:** Intermittent `OperationalError`, broken pipe errors, or corrupted query results under load.

### Pitfall 5: Missing .env File in Production
**What goes wrong:** `os.environ["DATABASE_URL"]` raises `KeyError` if `.env` is not present and the env var is not set via systemd or shell.
**Why it happens:** `.env` file is git-ignored (correctly), so it doesn't deploy automatically.
**How to avoid:** In production (systemd unit file), set `Environment=DATABASE_URL=...` directly. `load_dotenv()` is a no-op when `.env` doesn't exist and the env var is already set. Alternatively, use `os.environ.get("DATABASE_URL")` with a clear error message.
**Warning signs:** App crashes on startup with `KeyError: 'DATABASE_URL'`.

## Code Examples

Verified patterns from official sources:

### Executing Core Queries with text()
```python
# Source: SQLAlchemy 2.0 docs + CONTEXT.md decision
from sqlalchemy import text
from gbgolf.db import db

# Insert a fetch record
result = db.session.execute(
    text("""
        INSERT INTO fetches (tournament_name, fetched_at, player_count, source, tour)
        VALUES (:tournament_name, :fetched_at, :player_count, :source, :tour)
        RETURNING id
    """),
    {
        "tournament_name": "Arnold Palmer Invitational",
        "fetched_at": datetime.now(UTC),
        "player_count": 156,
        "source": "datagolf",
        "tour": "pga",
    }
)
fetch_id = result.scalar_one()
db.session.commit()
```

### Bulk Insert Projections
```python
# Source: SQLAlchemy 2.0 tutorial on INSERT
from sqlalchemy import text
from gbgolf.db import db

rows = [
    {"fetch_id": fetch_id, "player_name": "Scottie Scheffler", "projected_score": 68.5},
    {"fetch_id": fetch_id, "player_name": "Rory McIlroy", "projected_score": 69.2},
    # ...
]

db.session.execute(
    text("""
        INSERT INTO projections (fetch_id, player_name, projected_score)
        VALUES (:fetch_id, :player_name, :projected_score)
    """),
    rows,
)
db.session.commit()
```

### Query Latest Projections
```python
# Source: SQLAlchemy 2.0 SELECT tutorial
from sqlalchemy import text
from gbgolf.db import db

result = db.session.execute(
    text("""
        SELECT p.player_name, p.projected_score, f.tournament_name, f.fetched_at
        FROM projections p
        JOIN fetches f ON p.fetch_id = f.id
        WHERE f.id = (SELECT MAX(id) FROM fetches)
        ORDER BY p.projected_score ASC
    """)
)
rows = result.mappings().all()
# Each row is a dict-like RowMapping: row["player_name"], row["projected_score"], etc.
```

### .env File Template
```bash
# .env.example (committed to version control)
# Copy to .env and fill in real values
DATABASE_URL=postgresql://user:password@localhost:5432/gbgolf
DATAGOLF_API_KEY=your-api-key-here
SECRET_KEY=change-this-to-a-random-string
```

### .gitignore Addition
```
# Environment secrets
.env
```

### Test Fixture with SQLite In-Memory
```python
# tests/conftest.py addition
import pytest
from gbgolf.web import create_app
from gbgolf.db import db as _db

@pytest.fixture
def app():
    """Create app with in-memory SQLite for testing."""
    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True

    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

@pytest.fixture
def db_session(app):
    """Provide a transactional database session for tests."""
    with app.app_context():
        yield _db.session
        _db.session.rollback()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `session.query(Model)` (legacy) | `session.execute(select(Model))` | SQLAlchemy 2.0 (Jan 2023) | Phase 8 uses `text()` queries per CONTEXT.md decision, so this is moot but good to know |
| `SQLALCHEMY_TRACK_MODIFICATIONS = True` | Disabled by default in Flask-SQLAlchemy 3.0 | Flask-SQLAlchemy 3.0 (2023) | No action needed -- default is already correct |
| `psycopg2` requiring C compiler | `psycopg2-binary` pre-compiled wheels | Available since psycopg2 2.7 | Use `-binary` for deployment simplicity |
| Manual `MetaData()` for Core tables | `db.Table()` auto-binds to Flask-SQLAlchemy metadata | Flask-SQLAlchemy 3.0 | Simpler table definitions, automatic bind support |

**Deprecated/outdated:**
- `SQLALCHEMY_COMMIT_ON_TEARDOWN`: Removed in Flask-SQLAlchemy 3.0. Use explicit `db.session.commit()`.
- `db.engine` access outside app context: Raises error in Flask-SQLAlchemy 3.x. Always use within `app.app_context()` or during a request.

## Open Questions

1. **PostgreSQL already installed on VPS?**
   - What we know: VPS is Hostinger KVM 2 running Ubuntu 24.04. App currently has no database.
   - What's unclear: Whether PostgreSQL is already installed and a `gbgolf` database exists.
   - Recommendation: Phase 8 plan should include a task to verify/install PostgreSQL on the VPS. For local development, developers need a local PostgreSQL instance or can use SQLite for testing only.

2. **FLASK_APP environment variable for CLI commands**
   - What we know: Flask-Migrate CLI requires `FLASK_APP` to locate the app factory.
   - What's unclear: Current `FLASK_APP` setting in the project.
   - Recommendation: Set `FLASK_APP=gbgolf.web:create_app` in `.env` or document it in `.env.example`. Flask auto-discovers `load_dotenv()` from python-dotenv if installed.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x (already configured) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FETCH-05 | Tables exist with correct columns (player_name, projected_score, tournament_name, fetch_timestamp via FK) | integration | `pytest tests/test_db.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_db.py` -- covers FETCH-05: verify table creation, column types, FK constraint, cascade delete
- [ ] Update `tests/conftest.py` -- add `app` fixture with SQLite in-memory DB and `db_session` fixture
- [ ] Ensure `create_app()` handles missing `DATABASE_URL` gracefully in test mode (SQLite fallback or test override)

## Sources

### Primary (HIGH confidence)
- [Flask-SQLAlchemy 3.1.x Models and Tables](https://flask-sqlalchemy.readthedocs.io/en/stable/models/) -- db.Table Core-style definitions
- [Flask-SQLAlchemy 3.1.x Configuration](https://flask-sqlalchemy.readthedocs.io/en/stable/config/) -- SQLALCHEMY_DATABASE_URI, ENGINE_OPTIONS
- [Flask-SQLAlchemy 3.1.x Quick Start](https://flask-sqlalchemy.readthedocs.io/en/stable/quickstart/) -- db.session.execute() usage
- [Flask-Migrate documentation](https://flask-migrate.readthedocs.io/) -- init/migrate/upgrade workflow, app factory pattern
- [SQLAlchemy 2.0 MetaData docs](https://docs.sqlalchemy.org/en/20/core/metadata.html) -- Table, Column, ForeignKey definitions
- [SQLAlchemy 2.0 Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html) -- pool_pre_ping, NullPool, forked worker guidance

### Secondary (MEDIUM confidence)
- [SQLAlchemy Cascade Deletes](https://docs.sqlalchemy.org/en/20/orm/cascades.html) -- ondelete="CASCADE" on ForeignKey
- [python-dotenv PyPI](https://pypi.org/project/python-dotenv/) -- version 1.2.2, load_dotenv() behavior
- [David Caron: SQLAlchemy connection pool with threads and processes](https://davidcaron.dev/sqlalchemy-multiple-threads-and-processes/) -- Gunicorn forking analysis

### Tertiary (LOW confidence)
- None -- all findings verified against official documentation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries are well-established Flask ecosystem standards with current PyPI versions verified
- Architecture: HIGH -- patterns verified against official Flask-SQLAlchemy 3.1.x and Flask-Migrate documentation
- Pitfalls: HIGH -- common issues documented across multiple official sources (SQLAlchemy docs, Flask-SQLAlchemy docs)

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable ecosystem, no breaking changes expected)
