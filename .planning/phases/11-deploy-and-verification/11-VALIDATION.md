---
phase: 11
slug: deploy-and-verification
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | FETCH-01 | unit | `python -m pytest tests/ -x -q` | ✅ | ⬜ pending |
| 11-01-02 | 01 | 1 | FETCH-01 | unit | `python -m pytest tests/ -x -q` | ✅ | ⬜ pending |
| 11-01-03 | 01 | 2 | SRC-01 | manual | see Manual-Only | N/A | ⬜ pending |
| 11-01-04 | 01 | 2 | SRC-02 | manual | see Manual-Only | N/A | ⬜ pending |
| 11-01-05 | 01 | 2 | SRC-03 | manual | see Manual-Only | N/A | ⬜ pending |
| 11-01-06 | 01 | 2 | SRC-05 | manual | see Manual-Only | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Cron job fires on schedule on VPS | FETCH-01 | Requires live VPS + cron scheduler | SSH to VPS, wait for cron window, check fetch log for success entry with player count and tournament name |
| Both projection sources produce correct optimizer results | SRC-01/SRC-02 | Requires live deployed app | Navigate to gameblazers.silverreyes.net/golf, test DataGolf source and CSV upload, verify optimizer output |
| PostgreSQL connection pool bounded under use | SRC-03 | Requires live database introspection | Run `docker exec <container> psql -U gbgolf -c "SELECT count(*) FROM pg_stat_activity WHERE datname='gbgolf';"` and verify pool size stays within expected limits |
| Staleness label shows correct tournament name and relative age | SRC-05 | Requires live UI inspection | Check staleness label in both current-week and prior-week states; verify tournament name and relative time text |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
