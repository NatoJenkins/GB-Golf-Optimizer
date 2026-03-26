---
phase: 10-projection-source-selector
verified: 2026-03-25T12:00:00Z
status: human_needed
score: 14/14 must-haves verified
human_verification:
  - test: "Run app, visit http://127.0.0.1:5000/ with empty DB"
    expected: "Auto radio is disabled/dimmed, Upload CSV is selected, 'No projections available yet' appears below radio buttons"
    why_human: "CSS opacity and disabled visual state cannot be verified programmatically"
  - test: "Seed DB (fetch-projections CLI), reload page"
    expected: "Auto radio enabled and selected, staleness label shows tournament name and relative age, Projections CSV zone hidden"
    why_human: "Visual layout and default selection state require browser verification"
  - test: "Click 'Upload CSV' radio"
    expected: "Projections CSV upload zone appears, staleness label hides"
    why_human: "JS DOM toggle behavior requires browser interaction"
  - test: "Click 'Auto' radio"
    expected: "Projections CSV upload zone hides, staleness label returns"
    why_human: "JS DOM toggle behavior requires browser interaction"
  - test: "Upload roster CSV with Auto selected, click 'Generate Lineups'"
    expected: "Lineups generated using DB projections (no projections CSV needed)"
    why_human: "End-to-end DB-sourced optimizer result requires live app with populated DB"
---

# Phase 10: Projection Source Selector Verification Report

**Phase Goal:** Add a projection source selector so users can choose between auto-fetched DB projections and a manually uploaded CSV file.
**Verified:** 2026-03-25
**Status:** human_needed (all automated checks passed; 5 visual/interactive items need browser verification)
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | load_projections_from_db() returns dict[str, float] with normalized player name keys | VERIFIED | gbgolf/data/__init__.py lines 65-82: queries fetches, normalizes via normalize_name(), returns dict comprehension |
| 2 | validate_pipeline_auto() produces the same ValidationResult shape as validate_pipeline() | VERIFIED | gbgolf/data/__init__.py lines 85-111: identical structure, returns ValidationResult(valid_cards, excluded, projection_warnings=[]) |
| 3 | GET / queries DB for latest fetch and passes db_has_projections + latest_fetch to template | VERIFIED | routes.py line 97: render_template("index.html", **_db_template_vars()); _db_template_vars() always returns both keys |
| 4 | POST / with projection_source=auto loads projections from DB and runs optimizer | VERIFIED | routes.py lines 104, 137-138: reads projection_source from form, calls validate_pipeline_auto(roster_tmp, config_path) |
| 5 | POST / with projection_source=csv follows the existing CSV upload path unchanged | VERIFIED | routes.py lines 139-145: else branch saves projections file and calls validate_pipeline() as before |
| 6 | POST / with projection_source=auto and empty DB returns a user-friendly error | VERIFIED | data/__init__.py line 74 raises ValueError; routes.py line 164-165 catches and renders error; test_auto_source_empty_db_error passes |
| 7 | Every render_template() call includes db_has_projections and latest_fetch | VERIFIED | routes.py: 11 render_template calls confirmed, all use **_db_template_vars() |
| 8 | User sees Auto and Upload CSV radio buttons on the optimizer page | VERIFIED | index.html lines 39-48: input[name="source_radio"][value="auto"] and input[name="source_radio"][value="csv"] present |
| 9 | When Auto is selected, the Projections CSV upload zone is hidden | VERIFIED | index.html line 78: div#projections-zone has style="display:none" when db_has_projections; JS toggle at line 437 hides on radio change |
| 10 | Auto radio is disabled with 'No projections available yet' when DB is empty | VERIFIED | index.html lines 41, 62: disabled attr conditional; "No projections available yet" div present; test_auto_disabled_empty_db passes |
| 11 | Staleness label shows tournament name and relative fetch age when Auto is selected | VERIFIED | index.html lines 52-60: renders latest_fetch.tournament_name and days_ago; test_staleness_label_rendered passes |
| 12 | Switching from Auto to Upload CSV clears any previously selected projections file | VERIFIED | index.html JS lines 436-454: projFileInput.value = '' on switch to auto; projZone shown on switch to csv |
| 13 | Unmatched player warnings appear for roster players not found in DB projections | VERIFIED | validate_pipeline_auto uses match_projections() which produces excluded records; test_auto_source_unmatched_players passes |
| 14 | All 8 new tests pass green | VERIFIED | pytest tests/test_web.py: 40 passed (includes all 8 new tests); full suite: 115 passed |

**Score:** 14/14 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `gbgolf/data/__init__.py` | load_projections_from_db and validate_pipeline_auto functions | VERIFIED | Both functions present, substantive, in __all__; imports from sqlalchemy text and gbgolf.db |
| `gbgolf/web/routes.py` | Source-aware GET/POST route with DB query helper | VERIFIED | _get_latest_fetch(), _db_template_vars(), projection_source branching all present |
| `gbgolf/web/templates/index.html` | Source selector radio buttons, staleness label, hidden input, projections zone toggle | VERIFIED | All elements present with correct Jinja2 conditionals and JS toggle |
| `gbgolf/web/static/style.css` | CSS classes for source selector, staleness label, disabled state | VERIFIED | .source-selector, .source-radio, .source-radio:has(input[disabled]), .staleness-label, .staleness-label.stale all present |
| `tests/test_web.py` | 8 new test functions covering SRC-01 through SRC-05 | VERIFIED | All 8 functions present at lines 618-728, db_client fixture at 598, _seed_projections at 552 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| gbgolf/data/__init__.py | gbgolf/db.py | db.session.execute(text(...)) | VERIFIED | Line 70: db.session.execute(text("SELECT id FROM fetches...")) |
| gbgolf/data/__init__.py | gbgolf/data/matching.py | normalize_name() on DB player names | VERIFIED | Line 82: normalize_name(r["player_name"]) in dict comprehension |
| gbgolf/web/routes.py | gbgolf/data/__init__.py | validate_pipeline_auto() call in POST handler | VERIFIED | Line 138: validation = validate_pipeline_auto(roster_tmp, config_path) |
| gbgolf/web/routes.py | gbgolf/db.py | _get_latest_fetch() DB query | VERIFIED | Lines 61-63: db.session.execute(text("SELECT tournament_name, fetched_at FROM fetches...")) |
| gbgolf/web/templates/index.html | gbgolf/web/routes.py | Template variables db_has_projections and latest_fetch | VERIFIED | index.html uses db_has_projections in 5 conditionals; routes.py passes via _db_template_vars() on every render_template |
| gbgolf/web/templates/index.html | gbgolf/web/routes.py | Hidden input projection_source submitted to POST handler | VERIFIED | index.html line 50: name="projection_source"; routes.py line 104: request.form.get("projection_source", "csv") |
| tests/test_web.py | gbgolf/web/routes.py | Flask test client POST requests verify route behavior | VERIFIED | test_post_auto_source_uses_db and test_auto_source_empty_db_error use client.post() with projection_source field |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| SRC-01 | 10-02-PLAN | User can select "DataGolf" or "Upload CSV" as the projection source | SATISFIED | Radio buttons in index.html; hidden input submitted to POST; test_source_selector_rendered and test_projection_source_hidden_input pass |
| SRC-02 | 10-01-PLAN, 10-02-PLAN | When "DataGolf" selected, optimizer uses most recently stored DB projections | SATISFIED | load_projections_from_db() queries latest fetch by fetched_at DESC; validate_pipeline_auto() uses it; test_post_auto_source_uses_db passes |
| SRC-03 | 10-02-PLAN | UI displays stored tournament name and relative fetch age when DataGolf selected | SATISFIED | index.html staleness-label shows latest_fetch.tournament_name and days_ago; test_staleness_label_rendered passes |
| SRC-04 | 10-01-PLAN, 10-02-PLAN | If no projections fetched, DataGolf option disabled with "No projections available yet" | SATISFIED | index.html disabled conditional + fallback div; test_auto_disabled_empty_db and test_auto_source_empty_db_error pass |
| SRC-05 | 10-02-PLAN | Unmatched player warnings shown for roster players not in DB projections | SATISFIED | validate_pipeline_auto uses match_projections() producing excluded records; test_auto_source_unmatched_players passes |

No orphaned requirements — all 5 SRC requirements (SRC-01 through SRC-05) appear in plan frontmatter and are covered by implementation.

### Anti-Patterns Found

No anti-patterns detected. Scanned gbgolf/data/__init__.py, gbgolf/web/routes.py, gbgolf/web/templates/index.html, and gbgolf/web/static/style.css for: TODO/FIXME/HACK/PLACEHOLDER comments, empty implementations (return null/return {}), console.log-only handlers. All clean.

### Human Verification Required

#### 1. Empty DB disabled state visual

**Test:** Start the app with empty DB, visit http://127.0.0.1:5000/. Confirm "Auto" radio is visually disabled/dimmed (0.35 opacity via .source-radio:has(input[disabled])), "Upload CSV" is selected, and "No projections available yet" text appears below radio buttons.
**Expected:** Auto radio at 35% opacity, Upload CSV pre-selected, red/muted message visible below selector
**Why human:** CSS :has() pseudo-class disabled opacity and visual disabled state cannot be tested programmatically

#### 2. Populated DB default state visual

**Test:** Seed DB by running the fetch-projections CLI command, reload the page. Confirm "Auto" radio is now enabled and selected, staleness label shows tournament name and relative age, and the Projections CSV upload zone is hidden by default.
**Expected:** Auto selected, tournament name + "fetched N days ago" visible, Projections zone not visible
**Why human:** Default radio selection and section visibility on page load require browser verification

#### 3. Radio toggle — CSV

**Test:** With populated DB (Auto selected by default), click the "Upload CSV" radio. Confirm Projections CSV upload zone appears and staleness label hides.
**Expected:** Projections zone becomes visible, staleness text disappears
**Why human:** JS DOM toggle behavior (display changes) requires interactive browser testing

#### 4. Radio toggle — Auto

**Test:** After clicking Upload CSV (step 3), click "Auto" radio. Confirm Projections CSV zone hides and staleness label returns.
**Expected:** Projections zone hides, staleness text reappears
**Why human:** JS DOM toggle requires interactive browser testing; also verifies projFileInput.value = '' clears any selected file

#### 5. End-to-end lineup generation from DB projections

**Test:** With populated DB and Auto selected, upload a roster CSV only (no projections CSV), click "Generate Lineups". Confirm lineups are generated using DB projections.
**Expected:** Lineup results shown without requiring projections CSV upload
**Why human:** Requires live app with real DB projections to verify full optimizer flow with DB source

### Gaps Summary

No gaps. All automated checks passed. The 14 observable truths are satisfied by substantive, wired implementations. The 5 human verification items are routine UI and visual confirmation tasks that are standard for any frontend feature — they do not indicate missing implementation.

---

_Verified: 2026-03-25_
_Verifier: Claude (gsd-verifier)_
