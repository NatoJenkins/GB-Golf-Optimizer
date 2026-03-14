---
phase: 5
slug: serialization-and-re-optimize-route
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
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
| 5-01-01 | 01 | 0 | UI-02 | integration | `pytest tests/test_web.py::test_reoptimize_returns_results -x` | ❌ W0 | ⬜ pending |
| 5-01-02 | 01 | 0 | UI-02 | integration | `pytest tests/test_web.py::test_reoptimize_layout_identical -x` | ❌ W0 | ⬜ pending |
| 5-01-03 | 01 | 0 | UI-02 | integration | `pytest tests/test_web.py::test_reoptimize_missing_card_pool -x` | ❌ W0 | ⬜ pending |
| 5-01-04 | 01 | 0 | UI-02 | integration | `pytest tests/test_web.py::test_reoptimize_malformed_card_pool -x` | ❌ W0 | ⬜ pending |
| 5-01-05 | 01 | 0 | UI-02 | integration | `pytest tests/test_web.py::test_reoptimize_uses_session_constraints -x` | ❌ W0 | ⬜ pending |
| 5-01-06 | 01 | 0 | UI-02 | integration | `pytest tests/test_web.py::test_reoptimize_button_rendered -x` | ❌ W0 | ⬜ pending |
| 5-01-07 | 01 | 0 | UI-02 | integration | `pytest tests/test_web.py::test_reoptimize_button_absent_on_get -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_web.py::test_reoptimize_*` — 7 new test stubs for UI-02 (add to existing file)

*Existing infrastructure covers all other needs. No new config, no new fixture files — `conftest.py` and existing `client` fixture are sufficient.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Re-Optimize button is visually prominent above lineup results | UI-02 | Visual/UX check | After upload, verify button appears above lineups at correct position |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
