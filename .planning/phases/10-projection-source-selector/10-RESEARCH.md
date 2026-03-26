# Phase 10: Projection Source Selector - Research

**Researched:** 2026-03-25
**Domain:** Flask web layer (routes + Jinja2 template + vanilla JS) + SQLAlchemy Core DB reads
**Confidence:** HIGH

## Summary

Phase 10 adds a projection source selector to the optimizer UI. Users choose between "Auto" (DataGolf projections from the database) and "Upload CSV" before running the optimizer. The implementation touches three layers: the Jinja2 template (radio buttons, staleness label, show/hide toggle), the Flask route (GET: DB query for latest fetch; POST: branch on `projection_source`), and the data pipeline (new function to load projections from DB as a `dict[str, float]` compatible with `match_projections()`).

The existing codebase is well-structured for this change. The `validate_pipeline()` function calls `load_cards()` which calls `parse_projections_csv()` to produce a `dict[str, float]` of normalized player names to scores. The DB already stores player names in display format ("First Last") and projected scores. The cleanest approach is to add a `load_cards_from_db()` variant that reads projections from the DB, normalizes names, and feeds the same `match_projections()` function -- then a `validate_pipeline_auto()` that uses it instead of the CSV path. This avoids modifying the existing CSV pipeline at all.

**Primary recommendation:** Add `load_projections_from_db()` to `gbgolf/data/__init__.py` that returns `dict[str, float]` (same shape as `parse_projections_csv()` output), then add a `validate_pipeline_auto()` function that replaces only the projections-loading step. Keep the existing CSV pipeline completely untouched.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Source selector UI:** Radio buttons -- two labeled options "Auto" and "Upload CSV" side by side
- **Position:** Top of the upload `<details>` section, before the Roster CSV row
- **Default:** "Auto" pre-selected on page load -- unless the DB is empty, in which case "Upload CSV" is pre-selected
- **CSV upload zone visibility:** When "Auto" selected, Projections CSV upload zone hides (`display:none` or JS toggle); when "Upload CSV" selected, zone shows with `required` attribute active
- **Switching behavior:** Switching back from Auto to Upload CSV clears any previously selected file
- **Hidden input:** Source communicated via `<input name="projection_source" value="auto"|"csv">` synced by JS on radio change
- **Staleness label placement:** Directly below the radio buttons, visible only when "Auto" selected
- **Staleness format:** `[Tournament Name] -- fetched X days ago`
- **Fresh vs stale threshold:** 7 days (< 7 = normal text; >= 7 = muted/dimmed color)
- **Staleness label loaded on page GET** -- route queries DB for latest fetch record
- **Disabled/empty state:** Auto radio disabled + visually dimmed; message "No projections available yet"; "Upload CSV" auto-selected; backend returns error if `projection_source=auto` received but DB empty
- **GET `/`:** query DB for latest fetch record, pass `latest_fetch` and `db_has_projections` to template
- **POST `/`:** read `projection_source` hidden field; if `auto`, load from DB; if `csv`, existing path unchanged
- **Unmatched player warnings (SRC-05):** same `validation.excluded` report regardless of source
- **Re-optimize:** no changes needed -- `/reoptimize` works from serialized card pool

### Claude's Discretion
- CSS styling for the selector row (spacing, label weight, radio visual style within dark theme)
- CSS class names for the staleness label and its muted/fresh states
- Exact JS implementation for show/hide toggle and required attribute toggling
- How to structure the DB query for latest fetch (single SELECT on `fetches` table, ORDER BY fetched_at DESC LIMIT 1)
- Whether `latest_fetch` is passed as a dict or a simple namedtuple to the template

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SRC-01 | User can select "DataGolf" or "Upload CSV" as projection source | Radio button UI pattern in template + hidden input + JS toggle logic |
| SRC-02 | When "DataGolf" selected, optimizer uses most recently stored DB projections | `load_projections_from_db()` function + `validate_pipeline_auto()` variant + route branching |
| SRC-03 | UI displays stored tournament name and relative fetch age | GET route DB query for latest fetch + staleness label in template with relative time formatting |
| SRC-04 | If no projections in DB, DataGolf option disabled with message | `db_has_projections` boolean passed to template + disabled attribute + fallback to Upload CSV |
| SRC-05 | Unmatched player warnings shown for DB projections | Same `apply_filters()` exclusion pipeline produces `validation.excluded` regardless of source |
</phase_requirements>

## Standard Stack

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flask | 3.x | Web framework | Already in use; route + template rendering |
| Flask-SQLAlchemy | 3.1.x | DB integration | Already in use; provides `db.session` for queries |
| SQLAlchemy Core | 2.x | Raw SQL via `text()` | Project pattern: no ORM, `db.session.execute(text(...))` |
| Jinja2 | 3.x | Template engine | Already in use via Flask |

### Supporting (no new dependencies)
No new packages required. All functionality uses existing stack.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| New `validate_pipeline_auto()` | Modify existing `validate_pipeline()` to accept optional dict | Modifying existing function risks breaking CSV path; separate function is safer |
| `humanize` library for "X days ago" | Manual `timedelta.days` calculation | Not worth a new dependency for one use case; `timedelta.days` is trivial |
| HTMX for dynamic toggle | Vanilla JS `display:none` toggle | Project uses vanilla JS only -- no libraries |

**Installation:**
```bash
# No new packages needed
```

## Architecture Patterns

### Integration Points (files to modify)

```
gbgolf/
  data/
    __init__.py          # ADD: load_projections_from_db(), validate_pipeline_auto()
  web/
    routes.py            # MODIFY: GET (add DB query), POST (add source branch)
    templates/
      index.html         # MODIFY: add source selector UI, staleness label, JS toggle
    static/
      style.css          # MODIFY: add source selector CSS
```

### Pattern 1: DB Projection Loading
**What:** New function that reads projections from the DB and returns the same `dict[str, float]` shape that `parse_projections_csv()` produces.
**When to use:** When `projection_source == "auto"` in the POST route.
**Example:**
```python
# In gbgolf/data/__init__.py
from datetime import datetime, timezone
from sqlalchemy import text
from gbgolf.db import db

def load_projections_from_db() -> dict[str, float]:
    """Load latest projections from DB. Returns {normalized_name: score}.

    Raises ValueError if no projections exist.
    """
    # Get latest fetch
    row = db.session.execute(
        text("SELECT id FROM fetches ORDER BY fetched_at DESC LIMIT 1")
    ).mappings().fetchone()
    if row is None:
        raise ValueError("No projections available -- please upload a CSV")

    fetch_id = row["id"]
    rows = db.session.execute(
        text("SELECT player_name, projected_score FROM projections WHERE fetch_id = :fid"),
        {"fid": fetch_id},
    ).mappings().all()

    return {normalize_name(p["player_name"]): p["projected_score"] for p in rows}
```

### Pattern 2: Validate Pipeline Auto Variant
**What:** A new `validate_pipeline_auto()` that takes `roster_path` + `config_path` (no projections_path) and loads projections from DB instead of CSV.
**When to use:** When the POST route receives `projection_source == "auto"`.
**Example:**
```python
def validate_pipeline_auto(roster_path: str, config_path: str) -> ValidationResult:
    """Validation pipeline using DB projections instead of CSV file."""
    cards = parse_roster_csv(roster_path)
    projections = load_projections_from_db()
    enriched = match_projections(cards, projections)
    contests = load_config(config_path)
    valid_cards, excluded = apply_filters(enriched)

    if contests:
        min_required = min(c.roster_size for c in contests)
        if len(valid_cards) < min_required:
            raise ValueError(
                f"Only {len(valid_cards)} valid card(s) found -- "
                f"smallest contest requires at least {min_required}. "
                f"Check your exclusion report."
            )

    return ValidationResult(valid_cards=valid_cards, excluded=excluded, projection_warnings=[])
```

### Pattern 3: GET Route DB Query for Staleness Label
**What:** Query the latest fetch record on GET to pass tournament name and fetch age to the template.
**When to use:** Every GET request to `/`.
**Example:**
```python
# In routes.py index() GET handler
from datetime import datetime, timezone
from sqlalchemy import text
from gbgolf.db import db

def _get_latest_fetch():
    """Query latest fetch record. Returns dict or None."""
    row = db.session.execute(
        text("SELECT tournament_name, fetched_at FROM fetches ORDER BY fetched_at DESC LIMIT 1")
    ).mappings().fetchone()
    if row is None:
        return None
    fetched_at = row["fetched_at"]
    # Handle timezone -- SQLite stores naive, PostgreSQL stores aware
    now = datetime.now(timezone.utc)
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)
    delta = now - fetched_at
    return {
        "tournament_name": row["tournament_name"],
        "days_ago": delta.days,
        "is_stale": delta.days >= 7,
    }
```

### Pattern 4: Template Radio Buttons + JS Toggle
**What:** Radio buttons with hidden input, JS show/hide of projections upload zone, staleness label display.
**When to use:** In the `<details id="upload-section">` element.
**Example:**
```html
<!-- Source selector row - inside upload-section details, before Roster CSV -->
<div class="form-row">
  <span class="form-row-heading">Projection Source</span>
  <div class="source-selector">
    <label class="source-radio">
      <input type="radio" name="source_radio" value="auto"
             {% if db_has_projections %}checked{% endif %}
             {% if not db_has_projections %}disabled{% endif %} />
      Auto
    </label>
    <label class="source-radio">
      <input type="radio" name="source_radio" value="csv"
             {% if not db_has_projections %}checked{% endif %} />
      Upload CSV
    </label>
  </div>
  <!-- Hidden input synced by JS -->
  <input type="hidden" name="projection_source" id="projection-source-input"
         value="{{ 'auto' if db_has_projections else 'csv' }}" />
  <!-- Staleness label -->
  {% if latest_fetch %}
  <div class="staleness-label{% if latest_fetch.is_stale %} stale{% endif %}"
       id="staleness-label">
    {{ latest_fetch.tournament_name }} &mdash; fetched {{ latest_fetch.days_ago }} day{{ 's' if latest_fetch.days_ago != 1 else '' }} ago
  </div>
  {% elif not db_has_projections %}
  <div class="staleness-label stale" id="staleness-label">No projections available yet</div>
  {% endif %}
</div>
```

### Anti-Patterns to Avoid
- **Modifying `validate_pipeline()`:** Do NOT add an optional parameter to the existing function. Create a new variant to avoid any risk to the working CSV path.
- **Writing projections to a temp CSV:** Do NOT write DB projections to a temp file and pass it to `parse_projections_csv()`. The dict output is the real interface; bypass the file I/O entirely.
- **AJAX/fetch for source switching:** Do NOT use async requests. The source selection is purely a client-side toggle; all data is already in the page from the GET response.
- **Storing source preference in session:** Do NOT persist the source selection. It resets on each page load based on DB state.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Relative time display | Complex time formatting library | `timedelta.days` from Python stdlib | One calculation: `(now - fetched_at).days` is all that's needed |
| Radio button state sync | Complex state management | Vanilla JS event listener on `change` | Two radio buttons = trivial JS; matches existing project patterns |
| Timezone-aware comparison | Custom timezone handling | Python `datetime.timezone.utc` + `replace(tzinfo=...)` for SQLite | SQLite stores naive datetimes; PostgreSQL stores aware. Handle both with one line |

**Key insight:** This phase is primarily a UI integration task with a thin data layer addition. The optimizer, filtering, and matching logic are all unchanged. The only new data code is a simple SELECT query that produces a dict.

## Common Pitfalls

### Pitfall 1: SQLite vs PostgreSQL DateTime Handling
**What goes wrong:** `fetched_at` from SQLite is timezone-naive; from PostgreSQL it's timezone-aware. Subtracting naive from aware raises `TypeError`.
**Why it happens:** The `fetches.fetched_at` column stores `datetime.now(UTC)` which is timezone-aware, but SQLite drops timezone info on storage.
**How to avoid:** Before computing `delta = now - fetched_at`, check `fetched_at.tzinfo is None` and add UTC if missing: `fetched_at = fetched_at.replace(tzinfo=timezone.utc)`.
**Warning signs:** `TypeError: can't subtract offset-naive and offset-aware datetimes` in tests (which use SQLite).

### Pitfall 2: Projections File Input `required` Attribute
**What goes wrong:** If the projections file input stays `required` when "Auto" is selected, the browser blocks form submission because no file was selected.
**Why it happens:** HTML5 form validation checks `required` on hidden inputs.
**How to avoid:** JS must remove the `required` attribute from the projections file input when "Auto" is selected, and add it back when "Upload CSV" is selected.
**Warning signs:** Form won't submit with "Auto" selected; browser shows "Please select a file" validation error.

### Pitfall 3: Server-Side Validation of projection_source
**What goes wrong:** If a malformed request sends `projection_source=auto` but the DB is empty, the route crashes with an unhandled error.
**Why it happens:** Client-side disabling of the Auto radio doesn't prevent manual form submission.
**How to avoid:** Backend must validate: if `projection_source == "auto"` and no projections in DB, return a user-friendly error message. The `load_projections_from_db()` function should raise `ValueError` which is already caught by the route's `except ValueError`.
**Warning signs:** 500 error when DB is empty and someone manually submits `projection_source=auto`.

### Pitfall 4: Name Normalization Mismatch
**What goes wrong:** DB stores display names ("First Last") but `match_projections()` expects normalized keys (lowercase, accent-stripped).
**Why it happens:** The fetcher stores `parse_datagolf_name()` output (display format), not `normalize_name()` output.
**How to avoid:** `load_projections_from_db()` must call `normalize_name()` on each `player_name` from the DB before building the dict. This is the same normalization that `parse_projections_csv()` applies to CSV names.
**Warning signs:** No roster players match DB projections; all cards excluded with "no projection found".

### Pitfall 5: Radio Button Default on POST Error
**What goes wrong:** If the POST returns an error (e.g., validation failure), the template re-renders but the radio button state and staleness label are missing because `db_has_projections` and `latest_fetch` weren't passed.
**Why it happens:** Error paths in the POST handler call `render_template("index.html", error=...)` without the DB context variables.
**How to avoid:** Every `render_template()` call (including error paths) must include `db_has_projections` and `latest_fetch`. Extract the DB query into a helper function called at the top of both GET and POST handlers.
**Warning signs:** After a validation error, the source selector disappears or defaults incorrectly.

## Code Examples

### DB Query for Latest Fetch (verified against existing schema)
```python
# Source: gbgolf/db.py schema + gbgolf/fetcher.py write_projections pattern
from sqlalchemy import text
from gbgolf.db import db

row = db.session.execute(
    text("""
        SELECT tournament_name, fetched_at
        FROM fetches
        ORDER BY fetched_at DESC
        LIMIT 1
    """)
).mappings().fetchone()
# row is None if DB is empty; otherwise dict-like with row["tournament_name"], row["fetched_at"]
```

### Loading Projections from DB (verified against existing match_projections interface)
```python
# Source: matching.py match_projections() expects dict[str, float] with normalized keys
from gbgolf.data.matching import normalize_name

rows = db.session.execute(
    text("SELECT player_name, projected_score FROM projections WHERE fetch_id = :fid"),
    {"fid": fetch_id},
).mappings().all()

projections = {normalize_name(r["player_name"]): r["projected_score"] for r in rows}
# This dict has the exact same shape as parse_projections_csv() output
```

### JS Radio Toggle (follows existing vanilla JS patterns in index.html)
```javascript
// Source: existing patterns in index.html (event listeners on checkboxes)
var radios = document.querySelectorAll('input[name="source_radio"]');
var hiddenInput = document.getElementById('projection-source-input');
var projZone = document.getElementById('projections-zone');
var projInput = document.getElementById('projections');
var stalenessLabel = document.getElementById('staleness-label');

radios.forEach(function(radio) {
  radio.addEventListener('change', function() {
    hiddenInput.value = radio.value;
    if (radio.value === 'auto') {
      projZone.style.display = 'none';
      projInput.removeAttribute('required');
      projInput.value = '';  // clear any selected file
      if (stalenessLabel) stalenessLabel.style.display = '';
    } else {
      projZone.style.display = '';
      projInput.setAttribute('required', '');
      if (stalenessLabel) stalenessLabel.style.display = 'none';
    }
  });
});
```

### CSS for Source Selector (follows existing dark theme variables)
```css
/* Source: style.css existing variables and .form-row pattern */
.source-selector {
  display: flex;
  gap: 1.2rem;
  margin-top: 0.4rem;
}
.source-radio {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.source-radio input[disabled] + span,
.source-radio:has(input[disabled]) {
  opacity: 0.35;
  cursor: not-allowed;
}
.staleness-label {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  color: var(--text);
  margin-top: 0.3rem;
}
.staleness-label.stale {
  color: var(--text-muted);
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| CSV-only projections | DB projections + CSV upload | Phase 10 | Users no longer need to manually prepare a projections CSV when DataGolf data is available |

**No deprecated/outdated patterns** -- this phase builds on the existing stable codebase.

## Open Questions

1. **`days_ago` display for sub-24-hour fetches**
   - What we know: `timedelta.days` returns 0 for fetches less than 24 hours old
   - What's unclear: Should the label say "fetched today" or "fetched 0 days ago"?
   - Recommendation: Use "fetched today" when `days_ago == 0`, "fetched 1 day ago" for 1, "fetched N days ago" for N >= 2. Simple conditional in the template.

2. **Multiple tournaments in fetches table**
   - What we know: `write_projections()` DELETEs old data for the same tournament before inserting, but different tournaments could coexist
   - What's unclear: Could there be rows for multiple tournaments (e.g., PGA + LIV)?
   - Recommendation: The query `ORDER BY fetched_at DESC LIMIT 1` returns the most recent fetch regardless of tournament, which is correct behavior. The fetcher currently only fetches PGA Tour data.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `python -m pytest tests/test_web.py -x -q` |
| Full suite command | `python -m pytest -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SRC-01 | Source selector radio buttons rendered on GET | unit (web) | `python -m pytest tests/test_web.py::test_source_selector_rendered -x` | Wave 0 |
| SRC-01 | Hidden input `projection_source` present in form | unit (web) | `python -m pytest tests/test_web.py::test_projection_source_hidden_input -x` | Wave 0 |
| SRC-02 | POST with `projection_source=auto` uses DB projections | integration | `python -m pytest tests/test_web.py::test_post_auto_source_uses_db -x` | Wave 0 |
| SRC-02 | `load_projections_from_db()` returns correct dict shape | unit | `python -m pytest tests/test_web.py::test_load_projections_from_db -x` | Wave 0 |
| SRC-03 | GET renders staleness label with tournament name and days ago | unit (web) | `python -m pytest tests/test_web.py::test_staleness_label_rendered -x` | Wave 0 |
| SRC-04 | Auto radio disabled when DB empty, "No projections available yet" shown | unit (web) | `python -m pytest tests/test_web.py::test_auto_disabled_empty_db -x` | Wave 0 |
| SRC-04 | POST with `projection_source=auto` and empty DB returns error | unit (web) | `python -m pytest tests/test_web.py::test_auto_source_empty_db_error -x` | Wave 0 |
| SRC-05 | Unmatched players reported when using DB projections | integration | `python -m pytest tests/test_web.py::test_auto_source_unmatched_players -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_web.py -x -q`
- **Per wave merge:** `python -m pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] New tests in `tests/test_web.py` covering SRC-01 through SRC-05 (8 test functions listed above)
- [ ] Test helper to seed DB with fetch + projection data for web tests (similar to `test_fetcher.py` pattern but using the `client` fixture)
- [ ] No new test files needed -- all tests go in existing `tests/test_web.py`

## Sources

### Primary (HIGH confidence)
- `gbgolf/web/routes.py` -- current GET/POST route structure, validate_pipeline call pattern
- `gbgolf/data/__init__.py` -- validate_pipeline interface, load_cards decomposition
- `gbgolf/data/matching.py` -- match_projections interface (dict[str, float] input), normalize_name
- `gbgolf/data/projections.py` -- parse_projections_csv output shape (dict[str, float])
- `gbgolf/data/filters.py` -- apply_filters produces excluded list (used for SRC-05)
- `gbgolf/db.py` -- fetches + projections table schema (columns, types, FK)
- `gbgolf/fetcher.py` -- write_projections pattern (how data enters DB), name normalization chain
- `gbgolf/web/templates/index.html` -- existing form structure, JS patterns, dark theme
- `gbgolf/web/static/style.css` -- CSS variable names, .form-row pattern
- `tests/test_web.py` -- existing test patterns for Flask client, CSV POST helpers
- `tests/conftest.py` -- app fixture with in-memory SQLite, db_session fixture
- `tests/test_fetcher.py` -- DB query patterns in tests, mock helpers

### Secondary (MEDIUM confidence)
- `.planning/phases/10-projection-source-selector/10-CONTEXT.md` -- all user decisions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies; all existing libraries
- Architecture: HIGH -- straightforward extension of existing patterns; all integration points verified by reading source code
- Pitfalls: HIGH -- identified from direct code analysis (timezone handling, required attribute, name normalization)

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable codebase, no external API changes expected)
