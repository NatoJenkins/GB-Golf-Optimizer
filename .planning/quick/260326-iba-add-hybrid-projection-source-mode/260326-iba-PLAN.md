---
phase: quick
plan: 260326-iba
type: execute
wave: 1
depends_on: []
files_modified:
  - gbgolf/data/__init__.py
  - gbgolf/web/routes.py
  - gbgolf/web/templates/index.html
  - tests/test_web.py
autonomous: true
must_haves:
  truths:
    - "User can select Hybrid radio when DB has projections"
    - "Hybrid mode accepts CSV upload and fills gaps from DB"
    - "CSV projections take priority over DB projections on conflict"
    - "Unmatched player report only flags players missing from BOTH sources"
    - "Existing csv and auto paths are unchanged"
  artifacts:
    - path: "gbgolf/data/__init__.py"
      provides: "validate_pipeline_hybrid() function"
      contains: "def validate_pipeline_hybrid"
    - path: "gbgolf/web/routes.py"
      provides: "hybrid branch in POST handler"
      contains: "hybrid"
    - path: "gbgolf/web/templates/index.html"
      provides: "Third radio button for hybrid source"
      contains: "value=\"hybrid\""
    - path: "tests/test_web.py"
      provides: "Tests for hybrid projection path"
      contains: "hybrid"
  key_links:
    - from: "gbgolf/web/routes.py"
      to: "gbgolf/data/__init__.py"
      via: "import and call validate_pipeline_hybrid"
      pattern: "validate_pipeline_hybrid"
    - from: "gbgolf/web/templates/index.html"
      to: "gbgolf/web/routes.py"
      via: "projection_source hidden input value"
      pattern: "value=\"hybrid\""
---

<objective>
Add a hybrid projection source mode: "Upload CSV + fill gaps from DataGolf". When selected,
user uploads a CSV but any roster players missing from the CSV get their projected_score
filled from the DataGolf DB projections. CSV takes priority on name conflict.

Purpose: Users with partial CSV projections (e.g., custom adjustments for top players) can
still get coverage for the full field via DB projections, maximizing the valid card pool.

Output: New `validate_pipeline_hybrid()` function, route branch, third radio button in UI,
and tests covering the hybrid path.
</objective>

<execution_context>
@E:/ClaudeCodeProjects/GBGolfOptimizer/.planning/quick/260326-iba-add-hybrid-projection-source-mode/260326-iba-PLAN.md
</execution_context>

<context>
@gbgolf/data/__init__.py
@gbgolf/data/matching.py
@gbgolf/data/projections.py
@gbgolf/data/filters.py
@gbgolf/data/models.py
@gbgolf/web/routes.py
@gbgolf/web/templates/index.html
@tests/test_web.py

<interfaces>
<!-- Key types and contracts the executor needs. -->

From gbgolf/data/__init__.py:
```python
def validate_pipeline(roster_path: str, projections_path: str, config_path: str) -> ValidationResult
def validate_pipeline_auto(roster_path: str, config_path: str) -> ValidationResult
def load_projections_from_db() -> dict[str, float]  # {normalized_name: score}
```

From gbgolf/data/projections.py:
```python
def parse_projections_csv(path: str) -> tuple[dict[str, float], list[str]]
# Returns (projections_dict, warnings) — keys are normalized player names
```

From gbgolf/data/matching.py:
```python
def match_projections(cards: list[Card], projections: dict[str, float]) -> list[Card]
def normalize_name(name: str) -> str
```

From gbgolf/data/models.py:
```python
@dataclass
class ValidationResult:
    valid_cards: list = field(default_factory=list)
    excluded: list = field(default_factory=list)
    projection_warnings: list = field(default_factory=list)
```

From gbgolf/data/filters.py:
```python
def apply_filters(cards: list[Card]) -> tuple[list[Card], list[ExclusionRecord]]
# Exclusion rule 3: projected_score is None -> "no projection found"
```

From gbgolf/web/routes.py:
```python
projection_source = request.form.get("projection_source", "csv")
# Currently branches on "auto" vs else (csv)
```

From tests/test_web.py:
```python
# Fixtures: client (basic), db_client (with DB tables)
# Helper: _seed_projections(app, players_scores, tournament_name, days_ago)
# Helper: _post_csvs(client, roster_csv, projections_csv)
# Constants: SAMPLE_ROSTER_CSV, SAMPLE_PROJECTIONS_CSV, _VALID_PLAYERS
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Add validate_pipeline_hybrid() and route branch</name>
  <files>gbgolf/data/__init__.py, gbgolf/web/routes.py, tests/test_web.py</files>
  <behavior>
    - Test: POST with projection_source=hybrid, CSV has 10 players, DB has all 30 -> returns 200 with lineup results (all 30 matched)
    - Test: POST with projection_source=hybrid, CSV has Player A at 80.0, DB has Player A at 72.5 -> Player A gets 80.0 (CSV wins)
    - Test: POST with projection_source=hybrid, CSV has all 30 players, DB empty -> still works (CSV-only fallback)
    - Test: POST with projection_source=hybrid, no projections file uploaded -> returns error "Projections file is required"
    - Test: POST with projection_source=hybrid, CSV missing some players, DB also missing those same players -> those players appear in exclusion report as "no projection found"
  </behavior>
  <action>
  **In `gbgolf/data/__init__.py`:**

  Add `validate_pipeline_hybrid()` function. Signature:
  ```python
  def validate_pipeline_hybrid(
      roster_path: str,
      projections_path: str,
      config_path: str,
  ) -> ValidationResult:
  ```

  Implementation:
  1. `cards = parse_roster_csv(roster_path)`
  2. `csv_projections, warnings = parse_projections_csv(projections_path)`
  3. Try `db_projections = load_projections_from_db()` — catch ValueError (empty DB) and use empty dict `{}` instead
  4. Merge: `merged = {**db_projections, **csv_projections}` — this gives CSV priority since it overwrites DB keys
  5. `enriched = match_projections(cards, merged)`
  6. `contests = load_config(config_path)`
  7. `valid_cards, excluded = apply_filters(enriched)`
  8. Same pool-size guard as existing functions
  9. Return `ValidationResult(valid_cards=valid_cards, excluded=excluded, projection_warnings=warnings)`

  Add to `__all__`: `"validate_pipeline_hybrid"`

  Do NOT modify `validate_pipeline()` or `validate_pipeline_auto()`.

  **In `gbgolf/web/routes.py`:**

  1. Add `validate_pipeline_hybrid` to the import from `gbgolf.data`
  2. In the `index()` POST handler, update the projection_source branching. Currently:
     ```python
     if projection_source == "auto":
         validation = validate_pipeline_auto(roster_tmp, config_path)
     else:
         # csv path...
     ```
     Change to:
     ```python
     if projection_source == "auto":
         validation = validate_pipeline_auto(roster_tmp, config_path)
     elif projection_source == "hybrid":
         if not projections_file or projections_file.filename == "":
             return render_template("index.html", error="Projections file is required.", **_db_template_vars())
         with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="wb") as pf:
             projections_file.save(pf)
             projections_tmp = pf.name
         validation = validate_pipeline_hybrid(roster_tmp, projections_tmp, config_path)
     else:
         # existing csv path unchanged
     ```
  3. Also update the top-of-POST validation for projections_file requirement. Currently it checks `if projection_source == "csv"`. Change to check `if projection_source in ("csv", "hybrid")` so both modes require the file upload.

  **In `tests/test_web.py`:**

  Add tests using the existing `db_client` fixture and `_seed_projections` helper. Create a partial projections CSV constant for hybrid tests:

  ```python
  # Partial projections CSV: only first 10 of 30 players
  _PARTIAL_PROJ_ROWS = [f"{p},80.0" for p, _, _ in _VALID_PLAYERS[:10]]
  PARTIAL_PROJECTIONS_CSV = "player,projected_score\n" + "\n".join(_PARTIAL_PROJ_ROWS) + "\n"
  ```

  Tests to add (all in a new section "Phase: Hybrid projection source"):

  1. `test_hybrid_fills_gaps_from_db` — Seed DB with all 30 players at 72.5, POST hybrid with PARTIAL_PROJECTIONS_CSV (10 players at 80.0). Assert 200, "The Tips" in HTML. This proves DB filled the 20 missing players.

  2. `test_hybrid_csv_takes_priority` — Seed DB with all 30 at 72.5. Create a CSV with just Player A at 99.0. POST hybrid. Assert 200. Deserialize card_pool_json from response and check Player A's projected_score is 99.0 (not 72.5). Use a regex or string search in the HTML for the projected score value.

  3. `test_hybrid_db_empty_still_works` — Do NOT seed DB. POST hybrid with full SAMPLE_PROJECTIONS_CSV. Assert 200, "The Tips" in HTML. Proves hybrid gracefully handles empty DB.

  4. `test_hybrid_no_projections_file_error` — POST with projection_source=hybrid but no projections file. Assert 200, "Projections file is required" in HTML.

  5. `test_hybrid_unmatched_from_both_sources` — Seed DB with the 30 standard players (not "Unmatched Player"). POST hybrid with SAMPLE_PROJECTIONS_CSV (also no "Unmatched Player") using EXCLUSION_ROSTER_CSV. Assert "Unmatched Player" in HTML and "no projection found" in HTML.

  Helper for hybrid POSTs:
  ```python
  def _post_hybrid(client, roster_csv, projections_csv):
      return client.post(
          "/",
          data={
              "roster": (io.BytesIO(roster_csv.encode("utf-8")), "roster.csv"),
              "projections": (io.BytesIO(projections_csv.encode("utf-8")), "projections.csv"),
              "projection_source": "hybrid",
          },
          content_type="multipart/form-data",
      )
  ```
  </action>
  <verify>
    <automated>cd E:/ClaudeCodeProjects/GBGolfOptimizer && python -m pytest tests/test_web.py -k hybrid -x -v</automated>
  </verify>
  <done>All 5 hybrid tests pass. validate_pipeline_hybrid() merges CSV-priority projections with DB fallback. Route correctly branches on projection_source=="hybrid". Existing csv and auto tests still pass (run full test_web.py to confirm).</done>
</task>

<task type="auto">
  <name>Task 2: Add hybrid radio button and JS toggle logic in UI</name>
  <files>gbgolf/web/templates/index.html, tests/test_web.py</files>
  <action>
  **In `gbgolf/web/templates/index.html`:**

  1. Add a third radio button between Auto and Upload CSV in the `.source-selector` div:
     ```html
     <label class="source-radio">
       <input type="radio" name="source_radio" value="hybrid"
              {% if not db_has_projections %}disabled{% endif %} />
       Hybrid
     </label>
     ```
     Place it after the Auto radio and before the Upload CSV radio. The hybrid radio is disabled when `db_has_projections` is false (same as auto), because there's no DB to fill gaps from.

  2. Update the JS source selector toggle. Currently the `change` handler on `sourceRadios` checks `radio.value === 'auto'` vs else (csv). Update to handle three states:

     ```javascript
     sourceRadios.forEach(function(radio) {
       radio.addEventListener('change', function() {
         sourceHidden.value = radio.value;
         if (radio.value === 'auto') {
           // Hide upload zone, show staleness, hide CSV hint
           if (projZone) projZone.style.display = 'none';
           if (projFileInput) {
             projFileInput.removeAttribute('required');
             projFileInput.value = '';
           }
           if (stalenessEl) stalenessEl.style.display = '';
           if (csvFormatHint) csvFormatHint.style.display = 'none';
         } else if (radio.value === 'hybrid') {
           // Show BOTH upload zone AND staleness label
           if (projZone) projZone.style.display = '';
           if (projFileInput) projFileInput.setAttribute('required', '');
           if (stalenessEl) stalenessEl.style.display = '';
           if (csvFormatHint) csvFormatHint.style.display = '';
         } else {
           // csv: show upload zone, hide staleness, show CSV hint
           if (projZone) projZone.style.display = '';
           if (projFileInput) projFileInput.setAttribute('required', '');
           if (stalenessEl) stalenessEl.style.display = 'none';
           if (csvFormatHint) csvFormatHint.style.display = '';
         }
       });
     });
     ```

  3. The hidden input default value logic is fine as-is (auto when db_has_projections, csv otherwise). Hybrid is only selectable via radio click, not a default.

  **In `tests/test_web.py`:**

  Add UI-focused tests in the same hybrid section:

  1. `test_hybrid_radio_rendered` — Seed DB, GET /. Assert `value="hybrid"` in HTML.

  2. `test_hybrid_radio_disabled_no_db` — Do NOT seed DB, GET /. Assert the hybrid radio input is present AND disabled. Check for `value="hybrid"` and that the surrounding context includes `disabled`.

  3. `test_hybrid_radio_enabled_with_db` — Seed DB, GET /. Assert `value="hybrid"` present and NOT disabled (check that within a reasonable snippet around `value="hybrid"`, the word `disabled` does NOT appear... or simply check that the rendered radio for hybrid does not have the disabled attribute by parsing the HTML around the hybrid radio).
  </action>
  <verify>
    <automated>cd E:/ClaudeCodeProjects/GBGolfOptimizer && python -m pytest tests/test_web.py -k hybrid -x -v && python -m pytest tests/test_web.py -x -v</automated>
  </verify>
  <done>Third "Hybrid" radio button renders correctly. Disabled when DB has no projections, enabled when it does. JS toggle shows both file upload zone and staleness label when hybrid is selected. All existing tests still pass — zero regression on csv and auto paths.</done>
</task>

</tasks>

<verification>
1. `python -m pytest tests/test_web.py -x -v` — all tests pass (existing + new hybrid tests)
2. Manual spot-check (optional): run `flask run`, verify three radio buttons visible, select Hybrid, confirm both upload zone and staleness label appear simultaneously
</verification>

<success_criteria>
- validate_pipeline_hybrid() exists and merges CSV (priority) + DB (fallback) projections
- Route branches correctly on projection_source=="hybrid"
- Third radio button visible in UI, disabled when no DB projections
- JS toggle shows both upload zone and staleness label for hybrid mode
- Unmatched player report only flags players missing from BOTH sources
- All existing tests pass unchanged — zero risk to csv/auto paths
- All new hybrid tests pass
</success_criteria>

<output>
After completion, record a brief summary of what was built and any decisions made.
</output>
