---
phase: 7
slug: polish
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `pytest tests/test_web.py -x -q` |
| **Full suite command** | `pytest -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_web.py -x -q`
- **After every plan wave:** Run `pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 7-01-01 | 01 | 0 | UI-05 | unit (HTML assertion) | `pytest tests/test_web.py::test_clear_all_button_rendered -x` | ❌ W0 | ⬜ pending |
| 7-01-02 | 01 | 0 | UI-05 | unit (HTML assertion) | `pytest tests/test_web.py::test_clear_all_button_absent_on_get -x` | ❌ W0 | ⬜ pending |
| 7-01-03 | 01 | 0 | UI-06 | unit (HTML assertion) | `pytest tests/test_web.py::test_constraint_count_element_rendered -x` | ❌ W0 | ⬜ pending |
| 7-01-04 | 01 | 0 | UI-06 | unit (HTML assertion) | `pytest tests/test_web.py::test_constraint_count_absent_on_get -x` | ❌ W0 | ⬜ pending |
| 7-01-05 | 01 | 0 | UI-06 | unit (HTML assertion) | `pytest tests/test_web.py::test_sort_headers_rendered -x` | ❌ W0 | ⬜ pending |
| 7-01-06 | 01 | 1 | UI-06 | unit + manual | `pytest tests/test_web.py -x -q` | ✅ after W0 | ⬜ pending |
| 7-02-01 | 02 | 1 | Sortable cols | unit + manual | `pytest tests/test_web.py -x -q` | ✅ after W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_web.py` — add 5 new test functions covering UI-05 and UI-06 (file exists, append only)
  - `test_clear_all_button_rendered`
  - `test_clear_all_button_absent_on_get`
  - `test_constraint_count_element_rendered`
  - `test_constraint_count_absent_on_get`
  - `test_sort_headers_rendered`
- [ ] No new test files, fixtures, or framework changes needed

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Constraint count updates instantly when checkbox toggled | UI-06 | Pure client-side JS — no server-observable state | Toggle a lock/exclude checkbox; verify count display updates immediately without page reload |
| Count hidden when all constraints cleared | UI-06 | Pure client-side JS | Uncheck all constraints; verify `#constraint-count` disappears |
| Clear All button unchecks all locks and excludes | UI-05 | Pure client-side JS | Check several locks/excludes; click Clear All; verify all unchecked and count shows 0 |
| Table rows reorder correctly on column header click | Sortable cols | Pure client-side JS | Click each column header; verify sort order and indicator arrow updates |
| Sort resets to Player A-Z after Re-Optimize | Sortable cols | Requires form submission + server round-trip | Sort by salary; click Re-Optimize; verify Player column is default sort again |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
