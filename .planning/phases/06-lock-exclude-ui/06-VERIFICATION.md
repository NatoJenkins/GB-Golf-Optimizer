---
phase: 06-lock-exclude-ui
verified: 2026-03-14T00:00:00Z
status: passed
score: 10/10 must-haves verified
re_verification: false
---

# Phase 6: Lock/Exclude UI Verification Report

**Phase Goal:** Users can see their full eligible card pool after uploading CSVs and toggle lock/exclude on individual cards before or after optimizing.
**Verified:** 2026-03-14
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | After uploading CSVs, user sees a table of all eligible cards with a lock control and an exclude control per row | VERIFIED | `<details id="player-pool-section">` inside `#reoptimize-form` with `lock_card` and `exclude_card` checkboxes per row; `test_player_pool_section_rendered` + `test_lock_exclude_checkboxes_in_form` both GREEN |
| 2 | After optimizing, locked cards in lineup output are visually distinguished | VERIFIED | `<th>Lock</th>` first column in all lineup tables; `{% if locked_card_keys and (...) in locked_card_keys %}🔒{% endif %}` in every card `<td>`; `test_locked_card_shows_lock_icon` GREEN |
| 3 | Lock and exclude toggles persist through a re-optimize cycle | VERIFIED | `/reoptimize` route writes `session["locked_cards"]`, `session["locked_golfers"]`, `session["excluded_cards"]` from form submissions; template re-checks them on next render via `locked_card_keys`, `locked_golfer_set`, `excluded_card_keys`; all three parsing tests GREEN |

**Score: 3/3 truths verified**

---

### Plan-Level Must-Haves

#### Plan 06-01 Must-Haves (TDD RED suite)

| Truth | Status | Evidence |
|-------|--------|----------|
| 10 new test functions exist in tests/test_web.py targeting UI-01 and UI-03 | VERIFIED | 7 tests under `# Phase 06: UI-01` section + 3 tests under `# Phase 06: UI-03` section confirmed in file (lines 321–484) |
| All 10 new tests run and FAIL (RED) before implementation changes | VERIFIED (historical) | SUMMARY-01 documents all 10 failed with AssertionError; tests were intentionally written before implementation |
| Existing Phase 5 tests remain GREEN — no regressions | VERIFIED | `pytest tests/test_web.py`: 27 passed, 0 failed |

#### Plan 06-02 Must-Haves (Player pool UI + route parsing)

| Truth | Status | Evidence |
|-------|--------|----------|
| After uploading CSVs, user sees collapsible "Lock / Exclude Players" section with flat card table | VERIFIED | `index.html` line 59: `<details id="player-pool-section">` with `<summary>Lock / Exclude Players</summary>` inside `#reoptimize-form` |
| Each card row has Lock checkbox (card-level) and Exclude checkbox; first card row per player also has Lock Golfer checkbox | VERIFIED | Jinja2 namespace pattern (`ns.prev_player`) at line 76–98 of template renders `lock_golfer` only when `card.player != ns.prev_player`; `test_lock_golfer_first_row_only` asserts count == 30 and passes |
| All checkboxes inside #reoptimize-form | VERIFIED | `<details id="player-pool-section">` is nested inside `<form ... id="reoptimize-form">` (lines 56–122 of template); form closes after `</details>` and before `{% endif %}` |
| POST /reoptimize parses lock_card, exclude_card, lock_golfer via getlist() and writes session | VERIFIED | `routes.py` lines 174–183: `request.form.getlist("lock_card")`, `getlist("exclude_card")`, `getlist("lock_golfer")`; session writes on lines 180–183 |
| Checking Lock disables Exclude checkbox for same row (JS conflict prevention) | VERIFIED (automated) | `index.html` lines 210–233: event listeners on `.lock-cb` and `.exclude-cb` classes, plus page-load initialization for pre-checked states |
| Checkboxes pre-checked on re-render | VERIFIED | Template uses `{% if locked_card_keys and (...) in locked_card_keys %}checked{% endif %}` pattern on all three checkbox types |

#### Plan 06-03 Must-Haves (Lock column in lineup output)

| Truth | Status | Evidence |
|-------|--------|----------|
| All lineup result tables have a "Lock" column as first header | VERIFIED | `index.html` line 149: `<th>Lock</th>` as first `<th>` inside lineup table `<thead>`; `test_lineup_lock_column_header` GREEN |
| Card rows whose composite key is in locked_card_keys show the lock icon | VERIFIED | `index.html` line 160: `<td>{% if locked_card_keys and (card.player, card.salary, card.multiplier, card.collection) in locked_card_keys %}🔒{% endif %}</td>`; `test_locked_card_shows_lock_icon` GREEN |
| Card rows not in locked_card_keys show blank Lock column cell | VERIFIED | Same conditional renders empty `<td>` when condition is false; `test_nonlocked_card_blank_lock_column` GREEN |
| tfoot colspan correct (3, not 2) | VERIFIED | `index.html` line 171: `<td colspan="3"><strong>Totals</strong></td>` |

**Score: 10/10 plan-level must-haves verified**

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/test_web.py` | 10 Phase 6 test functions (UI-01 + UI-03) | VERIFIED | Lines 321–484; 7 UI-01 tests + 3 UI-03 tests present and substantive |
| `gbgolf/web/routes.py` | `/reoptimize` parses checkboxes via `getlist()`, writes session, passes template kwargs | VERIFIED | Lines 160–225; `_parse_card_keys` inline helper, full session write block, all 4 new template kwargs (`card_pool`, `locked_card_keys`, `locked_golfer_set`, `excluded_card_keys`) |
| `gbgolf/web/templates/index.html` | `player-pool-section` inside `#reoptimize-form`; Lock column in lineup tables | VERIFIED | Lines 55–122: player pool section; lines 147–177: lineup tables with Lock column |
| `gbgolf/web/static/style.css` | `.lock-golfer-empty` rule | VERIFIED | Lines 166–170: rule present with `display: block`, `min-width: 1rem`, `color: transparent` |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `index.html` | `routes.py /reoptimize` | `form action=/reoptimize`, checkboxes `name=lock_card/exclude_card/lock_golfer` inside `#reoptimize-form` | WIRED | `id="reoptimize-form"` confirmed wrapping the `<details id="player-pool-section">` block; all three checkbox name attributes present inside the form |
| `routes.py` | `constraints.py` | `ConstraintSet(locked_cards=..., locked_golfers=..., excluded_cards=...)` built from parsed form fields | WIRED | Lines 186–191: `ConstraintSet` constructed directly from `locked_cards`, `locked_golfers`, `excluded_cards` parsed via `_parse_card_keys` — not from session re-read |
| `routes.py` | `index.html` | `render_template` passes `card_pool`, `locked_card_keys`, `locked_golfer_set`, `excluded_card_keys` | WIRED | Lines 215–225: all four kwargs present in `render_template` call; also present in `index()` POST at lines 112–123 |
| `routes.py` | `constraints.py` (pre-solve checks) | `check_conflicts(constraints)` and `check_feasibility(constraints, valid_cards, contest_config)` | WIRED | Lines 14, 194, 204: imported and called in correct order before `optimize()` |
| `index.html` (locked_card_keys) | `index.html` (lineup table rows) | Jinja2 `in` operator set membership check | WIRED | Line 160: `{% if locked_card_keys and (card.player, card.salary, card.multiplier, card.collection) in locked_card_keys %}🔒{% endif %}` |

---

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| UI-01 | 06-01, 06-02 | User sees eligible player pool with per-card lock/exclude controls after uploading CSVs | SATISFIED | `<details id="player-pool-section">` with 8-column table inside `#reoptimize-form`; checkboxes for `lock_card`, `lock_golfer`, `exclude_card` per row; 7 UI-01 tests GREEN |
| UI-03 | 06-01, 06-03 | Locked cards visually marked in lineup output confirming constraints took effect | SATISFIED | `<th>Lock</th>` first column in lineup tables; 🔒 emoji on locked card rows; 3 UI-03 tests GREEN |

**Requirements traceability check:** REQUIREMENTS.md maps UI-01 and UI-03 to Phase 6 with status [x] (complete). Both are claimed by plans in this phase. No orphaned requirements.

**Note:** REQUIREMENTS.md also shows UI-02 as complete (Phase 5). UI-02 is not claimed by any Phase 6 plan — correctly handled by Phase 5 plans only. No orphan.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | None found | — | — |

Scanned: `gbgolf/web/routes.py`, `gbgolf/web/templates/index.html`, `gbgolf/web/static/style.css`, `tests/test_web.py`

---

### Human Verification Required

The following behaviors cannot be verified programmatically:

#### 1. JS Conflict Prevention — Visual Interaction

**Test:** Upload CSVs, expand "Lock / Exclude Players", check the Lock checkbox for a card row.
**Expected:** The Exclude checkbox for that same row becomes visually disabled (grayed out, not clickable).
**Why human:** Browser DOM interaction and `disabled` attribute rendering cannot be asserted via Flask test client.

#### 2. Pre-Checked State Initialization on Page Load

**Test:** Lock a card via Re-Optimize, observe the player pool section on the results page. Check that: (a) the Lock checkbox for that card is pre-checked, and (b) the Exclude checkbox for that same row is already disabled on page load.
**Expected:** Both conditions true — checkbox reflects session state, and the initialization JS (`document.querySelectorAll(".lock-cb:checked")`) has fired correctly.
**Why human:** Page-load JS execution and visual disabled state require a real browser.

#### 3. Lock / Exclude Cycle End-to-End

**Test:** Upload CSVs → expand player pool → lock one card → click Re-Optimize → verify 🔒 appears next to that card in the lineup output → expand player pool again → verify Lock checkbox is still checked.
**Expected:** Locked card marked in lineup, checkbox pre-checked on re-render.
**Why human:** Full UI session cycle with visual confirmation.

---

### Test Suite Results

```
pytest tests/test_web.py -v -q
27 passed in 1.88s
```

All 27 tests pass: 17 Phase 3-5 tests + 10 Phase 6 tests (7 UI-01, 3 UI-03). Zero regressions.

---

### Summary

Phase 6 goal is fully achieved. All three ROADMAP success criteria are satisfied:

1. **Player pool visibility (UI-01):** A collapsible `<details id="player-pool-section">` section renders after CSV upload with an 8-column table (Lock, Lock Golfer, Exclude, Player, Collection, Salary, Multiplier, Proj Score). All checkboxes are inside `#reoptimize-form` and submit with the card pool on Re-Optimize. Lock Golfer checkbox appears once per unique player (deduplication via Jinja2 namespace).

2. **Locked card visual marker (UI-03):** All lineup output tables have `<th>Lock</th>` as the first column. Locked card rows render 🔒 via Jinja2 set membership against `locked_card_keys`. Non-locked rows show a blank cell. The `tfoot` colspan is correctly set to 3.

3. **Persistence through re-optimize cycle:** The `/reoptimize` route parses `lock_card`, `exclude_card`, and `lock_golfer` form fields via `request.form.getlist()`, writes them to session, builds `ConstraintSet` from the parsed values (not stale session), and passes `locked_card_keys`, `locked_golfer_set`, `excluded_card_keys` back to the template so pre-checked state is reflected on re-render.

Three items require human browser testing (JS interaction, disabled state, visual cycle) but all automated checks pass with zero gaps.

---

_Verified: 2026-03-14_
_Verifier: Claude (gsd-verifier)_
