---
phase: 8
slug: database-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (already configured) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 8-01-01 | 01 | 0 | FETCH-05 | integration | `pytest tests/test_db.py -x` | ❌ W0 | ⬜ pending |
| 8-01-02 | 01 | 1 | FETCH-05 | integration | `pytest tests/test_db.py -x -q` | ❌ W0 | ⬜ pending |
| 8-01-03 | 01 | 1 | FETCH-05 | integration | `pytest tests/test_db.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_db.py` — stubs covering FETCH-05: verify table creation, column types, FK constraint, cascade delete
- [ ] `tests/conftest.py` — add `app` fixture with SQLite in-memory DB and `db_session` fixture
- [ ] Ensure `create_app()` handles missing `DATABASE_URL` gracefully in test mode (SQLite fallback or test override)

*Wave 0 must be complete before Wave 1 tasks execute.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Flask app starts cleanly with PostgreSQL on production VPS | FETCH-05 | Requires live VPS + PostgreSQL credentials | SSH to VPS, set DATABASE_URL, run `flask db upgrade`, then `gunicorn` and confirm no startup errors |
| Gunicorn forked workers each get own connection pool | FETCH-05 | Requires multi-worker Gunicorn load test | Start `gunicorn -w 4`, run concurrent requests, confirm no `OperationalError` or broken pipe errors |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
