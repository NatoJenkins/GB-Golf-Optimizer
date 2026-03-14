---
phase: 3
slug: web-application-and-deployment
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `pytest tests/test_web.py -x -q` |
| **Full suite command** | `pytest -x -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_web.py -x -q`
- **After every plan wave:** Run `pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 0 | DISP-01 | unit | `pytest tests/test_web.py -x -q` | ❌ W0 | ⬜ pending |
| 3-xx-xx | TBD | 1 | DISP-01 | integration | `pytest tests/test_web.py::test_lineup_table_columns -x` | ❌ W0 | ⬜ pending |
| 3-xx-xx | TBD | 1 | DISP-01 | integration | `pytest tests/test_web.py::test_lineup_totals_row -x` | ❌ W0 | ⬜ pending |
| 3-xx-xx | TBD | 1 | DISP-02 | integration | `pytest tests/test_web.py::test_contest_sections_order -x` | ❌ W0 | ⬜ pending |
| 3-xx-xx | TBD | 1 | DISP-02 | integration | `pytest tests/test_web.py::test_lineups_grouped_by_contest -x` | ❌ W0 | ⬜ pending |
| 3-xx-xx | TBD | 1 | DISP-01 | integration | `pytest tests/test_web.py::test_infeasibility_notice_rendered -x` | ❌ W0 | ⬜ pending |
| 3-xx-xx | TBD | 1 | DISP-01 | integration | `pytest tests/test_web.py::test_exclusion_report_hidden_on_clean_run -x` | ❌ W0 | ⬜ pending |
| 3-xx-xx | TBD | 1 | DISP-01 | integration | `pytest tests/test_web.py::test_exclusion_report_content -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_web.py` — stubs for DISP-01, DISP-02 integration tests (all 7 automated tests listed above)
- [ ] `flask>=3.0` added to `[project.optional-dependencies].dev` in `pyproject.toml` (not currently listed)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Smoke test: GET `/golf/` returns HTTP 200 on live server | DEPL-01 | Requires live VPS with Nginx/Gunicorn/systemd deployed | `curl https://gameblazers.silverreyes.net/golf/` — expect 200 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
