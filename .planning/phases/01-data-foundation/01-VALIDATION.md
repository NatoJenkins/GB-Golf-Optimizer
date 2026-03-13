---
phase: 1
slug: data-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] — Wave 0 installs |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

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
| 1-01-01 | 01 | 0 | UPLD-01, UPLD-02, OPT-05, OPT-07, DATA-01, DATA-02, DATA-03 | unit | `pytest tests/ -x -q` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | UPLD-01 | unit | `pytest tests/test_roster.py -x` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 1 | UPLD-01 | unit | `pytest tests/test_roster.py::test_missing_column_fails -x` | ❌ W0 | ⬜ pending |
| 1-03-01 | 02 | 1 | UPLD-02 | unit | `pytest tests/test_projections.py -x` | ❌ W0 | ⬜ pending |
| 1-03-02 | 02 | 1 | UPLD-02 | unit | `pytest tests/test_projections.py::test_bad_row_skipped -x` | ❌ W0 | ⬜ pending |
| 1-04-01 | 02 | 1 | OPT-05 | unit | `pytest tests/test_matching.py::test_effective_value -x` | ❌ W0 | ⬜ pending |
| 1-04-02 | 02 | 1 | DATA-02 | unit | `pytest tests/test_filters.py::test_no_projection_excluded -x` | ❌ W0 | ⬜ pending |
| 1-05-01 | 02 | 1 | OPT-07 | unit | `pytest tests/test_config.py::test_valid_config -x` | ❌ W0 | ⬜ pending |
| 1-05-02 | 02 | 1 | OPT-07 | unit | `pytest tests/test_config.py::test_invalid_config -x` | ❌ W0 | ⬜ pending |
| 1-06-01 | 02 | 1 | DATA-01 | unit | `pytest tests/test_filters.py::test_zero_salary_excluded -x` | ❌ W0 | ⬜ pending |
| 1-06-02 | 02 | 1 | DATA-03 | unit | `pytest tests/test_filters.py::test_expired_excluded -x` | ❌ W0 | ⬜ pending |
| 1-06-03 | 02 | 1 | DATA-03 | unit | `pytest tests/test_filters.py::test_expires_today_included -x` | ❌ W0 | ⬜ pending |
| 1-07-01 | 02 | 2 | All | integration | `pytest tests/test_pipeline.py -x` | ❌ W0 | ⬜ pending |
| 1-07-02 | 02 | 2 | All | integration | `pytest tests/test_pipeline.py::test_cli_valid -x` | ❌ W0 | ⬜ pending |
| 1-07-03 | 02 | 2 | UPLD-01 | integration | `pytest tests/test_pipeline.py::test_cli_bad_roster -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — shared fixtures: sample CSV content as strings, tmp CSV file factory, sample valid ContestConfig dict
- [ ] `tests/test_roster.py` — covers UPLD-01
- [ ] `tests/test_projections.py` — covers UPLD-02
- [ ] `tests/test_matching.py` — covers OPT-05, DATA-02
- [ ] `tests/test_filters.py` — covers DATA-01, DATA-02, DATA-03
- [ ] `tests/test_config.py` — covers OPT-07
- [ ] `tests/test_pipeline.py` — integration coverage for all requirements
- [ ] `pyproject.toml` — project metadata + [tool.pytest.ini_options]
- [ ] Framework install: `pip install pytest pydantic python-dateutil`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Unmatched players report is human-readable | DATA-02 | Output format judgment | Run with intentionally unmatched player, review report format |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
