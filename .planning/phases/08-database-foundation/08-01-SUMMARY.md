---
phase: 08-database-foundation
plan: 01
subsystem: database
tags: [flask-sqlalchemy, flask-migrate, postgresql, python-dotenv, alembic, sqlalchemy-core]

# Dependency graph
requires:
  - phase: 07-polish
    provides: working Flask app factory with routes and test suite
provides:
  - SQLAlchemy db instance at gbgolf/db.py
  - fetches and projections table definitions (Core, no ORM)
  - Flask-Migrate migrations directory with initial schema
  - App factory wired with db.init_app, Migrate, load_dotenv
  - .env.example template for DATABASE_URL, DATAGOLF_API_KEY, SECRET_KEY
  - .gitignore excluding .env and Python artifacts
  - app and db_session test fixtures in conftest.py
affects: [09-datagolf-fetcher, 10-cli-integration, 11-deployment]

# Tech tracking
tech-stack:
  added: [flask-sqlalchemy>=3.1, flask-migrate>=4.1, psycopg2-binary>=2.9, python-dotenv>=1.0]
  patterns: [db.py module for SQLAlchemy instance, Core Table definitions, db.init_app in app factory, SQLite in-memory for tests, PRAGMA foreign_keys for SQLite FK enforcement]

key-files:
  created: [gbgolf/db.py, .env.example, .gitignore, tests/test_db.py, migrations/]
  modified: [gbgolf/web/__init__.py, pyproject.toml, tests/conftest.py]

key-decisions:
  - "SQLite in-memory fallback when DATABASE_URL not set (avoids KeyError in test/dev)"
  - "pool_pre_ping=True for Gunicorn forked worker safety"
  - "ON DELETE CASCADE at database level for fetches->projections FK"
  - "PRAGMA foreign_keys=ON in SQLite tests for FK constraint enforcement"

patterns-established:
  - "db.py module pattern: db = SQLAlchemy() at module level, Table definitions in same file"
  - "App factory DB wiring: load_dotenv() -> config -> db.init_app(app) -> Migrate(app, db)"
  - "Test fixtures: app fixture creates SQLite in-memory DB, db_session fixture yields transactional session"

requirements-completed: [FETCH-05]

# Metrics
duration: 6min
completed: 2026-03-25
---

# Phase 8 Plan 1: Database Foundation Summary

**PostgreSQL wiring via Flask-SQLAlchemy Core with fetches/projections tables, Flask-Migrate schema migrations, and python-dotenv secrets loading**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-25T21:47:08Z
- **Completed:** 2026-03-25T21:53:36Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments
- Two-table schema (fetches + projections) defined using SQLAlchemy Core Table objects with ON DELETE CASCADE FK
- App factory wired with db.init_app, Migrate, load_dotenv, and SQLALCHEMY_DATABASE_URI with SQLite fallback
- Flask-Migrate initialized with first migration script (revision 4938bf64fe7e) creating both tables
- 5 DB integration tests covering table creation, FK constraints, cascade deletes, and NOT NULL enforcement
- Full test suite (90 tests) passes with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Wave 0 -- Create test infrastructure and failing DB tests** - `dbbbe66` (test)
2. **Task 2: Install dependencies, create db.py, wire app factory, create .env.example and .gitignore** - `6c4644e` (feat)
3. **Task 3: Initialize Flask-Migrate and generate first migration** - `484a3d8` (chore)

_TDD flow: Task 1 (RED) wrote failing tests, Task 2 (GREEN) implemented code to pass them._

## Files Created/Modified
- `gbgolf/db.py` - SQLAlchemy instance and fetches/projections Core table definitions
- `gbgolf/web/__init__.py` - App factory updated with dotenv, SQLAlchemy, and Migrate initialization
- `pyproject.toml` - Added flask-sqlalchemy, flask-migrate, psycopg2-binary, python-dotenv dependencies
- `.env.example` - Template with DATABASE_URL, DATAGOLF_API_KEY, SECRET_KEY, FLASK_APP placeholders
- `.gitignore` - Excludes .env, __pycache__, IDE files, build artifacts
- `tests/test_db.py` - 5 DB integration tests (table existence, FK, cascade, NOT NULL)
- `tests/conftest.py` - Added app and db_session fixtures (all existing fixtures preserved)
- `migrations/` - Flask-Migrate directory with initial schema migration

## Decisions Made
- Used `os.environ.get("DATABASE_URL", "sqlite:///:memory:")` instead of `os.environ["DATABASE_URL"]` to avoid KeyError when running tests or local dev without a .env file (Pitfall 5 from RESEARCH.md)
- Added `pool_pre_ping=True` to SQLALCHEMY_ENGINE_OPTIONS for safe connection reuse under Gunicorn pre-fork workers
- Chose ON DELETE CASCADE at database level (not application level) since Core tables have no ORM relationship support
- Used `PRAGMA foreign_keys = ON` in SQLite test fixtures to enforce FK constraints that SQLite disables by default

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tasks completed as planned. Dependencies installed cleanly, migration auto-detected both tables correctly, all tests passed on first run.

## User Setup Required

None - no external service configuration required. The .env.example file is committed as a template; users copy it to .env and fill in real values before production deployment.

## Next Phase Readiness
- Database schema ready for Phase 9 (DataGolf Fetcher) to INSERT into fetches and projections tables
- App factory loads DATABASE_URL from .env automatically via python-dotenv
- Flask-Migrate ready for future schema changes (e.g., v1.3 user_id column addition)
- DataGolf API key placeholder in .env.example ready for Phase 9

## Self-Check: PASSED

All 8 files verified present. All 3 commit hashes verified in git log.

---
*Phase: 08-database-foundation*
*Completed: 2026-03-25*
