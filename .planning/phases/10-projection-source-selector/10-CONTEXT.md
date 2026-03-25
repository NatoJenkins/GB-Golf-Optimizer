# Phase 10: Projection Source Selector - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a projection source selector to the optimizer UI. Users pick "Auto" (DataGolf projections from the database) or "Upload CSV" before running the optimizer. When Auto is selected, projections are read from the database; the CSV upload zone hides. Display the stored tournament name and relative fetch age below the selector. Handle the empty-DB state by disabling the Auto option with an explanatory message.

Covers SRC-01, SRC-02, SRC-03, SRC-04, SRC-05.

</domain>

<decisions>
## Implementation Decisions

### Source selector UI
- **Style:** Radio buttons — two labeled options side by side
- **Labels:** "Auto" and "Upload CSV"
- **Position:** Top of the upload `<details>` section, before the Roster CSV row
- **Default:** "Auto" pre-selected on page load — unless the DB is empty, in which case "Upload CSV" is pre-selected

### CSV upload zone visibility
- When "Auto" is selected: Projections CSV upload zone hides completely (`display:none` or JS toggle)
- When "Upload CSV" is selected: Projections CSV zone shows; file input has `required` attribute active
- Switching back from Auto to Upload CSV: clears any previously selected file (clean state)
- Source is communicated to the backend via a hidden `<input name="projection_source" value="auto"|"csv">` synced by JS when the radio changes

### Staleness label
- Placement: Directly below the radio buttons, visible only when "Auto" is selected
- Format: `[Tournament Name] — fetched X days ago`
  - Example: `Arnold Palmer Invitational — fetched 8 days ago`
- **Fresh vs stale threshold:** 7 days
  - < 7 days old: normal text color
  - 7+ days old: muted/dimmed color to signal prior-week data
- Label is hidden (or absent from DOM) when "Upload CSV" is selected
- Loaded on page GET — the route queries the DB for the latest fetch record to populate this

### Disabled/empty state (DB has no projections)
- Auto radio: disabled attribute + visually dimmed
- Message below the disabled Auto option: `No projections available yet`
- "Upload CSV" is auto-selected instead — existing file-upload behavior is preserved
- Backend: if `projection_source=auto` is received but DB is empty, return an error: `No projections available — please upload a CSV`

### Backend routing
- **GET `/`**: query DB for latest fetch record (tournament_name, fetched_at); pass `latest_fetch` and `db_has_projections` to template
- **POST `/`**: read `projection_source` hidden field; if `auto`, load projections from DB and run validate_pipeline using them; if `csv`, existing file-upload path unchanged
- Unmatched player warnings (SRC-05): same `validation.excluded` report, populated regardless of source

### Re-optimize behavior
- No changes needed — `/reoptimize` works from the serialized card pool in the hidden form field; projected_scores are embedded at first-optimize time regardless of source. DataGolf source does not need to re-read the DB on re-optimize.

### Claude's Discretion
- CSS styling for the selector row (spacing, label weight, radio visual style within dark theme)
- CSS class names for the staleness label and its muted/fresh states
- Exact JS implementation for show/hide toggle and required attribute toggling
- How to structure the DB query for latest fetch (single SELECT on `fetches` table, ORDER BY fetched_at DESC LIMIT 1)
- Whether `latest_fetch` is passed as a dict or a simple namedtuple to the template

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — SRC-01 through SRC-05 (full projection source requirements)

### Project and state decisions
- `.planning/PROJECT.md` — Key Decisions table (Flask, PuLP, SQLAlchemy Core, no ORM, vanilla JS only)
- `.planning/STATE.md` — Accumulated Context > Decisions section (DB query pattern, session handling, normalize_name pipeline)

### Database schema (from Phase 8)
- `.planning/phases/08-database-foundation/08-CONTEXT.md` — fetches + projections table schema, column names
- `gbgolf/db.py` — Actual table definitions

### Fetcher and DB patterns (from Phase 9)
- `.planning/phases/09-datagolf-fetcher/09-CONTEXT.md` — DB write pattern, SQLAlchemy Core text() usage, normalize_name() call chain

### Existing UI patterns (template and routes)
- `gbgolf/web/templates/index.html` — Existing upload form structure, dark theme, vanilla JS patterns
- `gbgolf/web/routes.py` — GET/POST route structure, validate_pipeline call, card pool serialization

No external API specs required for this phase — DataGolf data is already in the DB from Phase 9.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `gbgolf/web/routes.py` `index()` GET: currently returns plain `render_template("index.html")` — needs to query DB for latest fetch info and pass `latest_fetch` + `db_has_projections` to template
- `gbgolf/web/routes.py` `index()` POST: existing CSV path stays intact; new `if projection_source == "auto"` branch loads projections from DB instead of the uploaded file
- `gbgolf/db.py` `fetches` + `projections` tables: Phase 10 reads from both — SELECT latest fetch + JOIN to projections for that fetch_id
- `gbgolf/data/validate_pipeline()`: currently takes two CSV file paths; Phase 10 needs a way to pass projections as in-memory data (list of dicts or a temp file) when DataGolf source is selected
- Existing unmatched player report (`validation.excluded`): already rendered in template — works unchanged for DataGolf source

### Established Patterns
- Vanilla JS only — no libraries; show/hide and required toggling follow existing checkbox JS patterns
- SQLAlchemy Core `text()` for all DB queries — no ORM
- Pydantic at boundary only — DB query results should return plain Python objects, not SQLAlchemy Row proxies
- `<details id="upload-section">` wraps the upload form — source selector goes at the top, inside this element
- `.form-row` CSS class for form rows — source selector row should use the same class for visual consistency

### Integration Points
- Template `<details id="upload-section">` → add source selector row at the top
- Template projections `<input type="file" name="projections" required>` → `required` toggled by JS based on radio state
- `routes.py` `index()` → add DB query on GET, add `projection_source` branch on POST
- `gbgolf/data/validate_pipeline()` → may need a variant that accepts an in-memory projections list rather than a CSV file path (researcher should investigate the cleanest approach)

</code_context>

<specifics>
## Specific Ideas

- Mockup confirmed by user:
  ```
  Projection Source
  [● Auto] [○ Upload CSV]
  Arnold Palmer Invitational — fetched 8 days ago

  Roster CSV
    [upload zone]

  [ Generate Lineups ]
  ```
- Stale data: dimmed/muted color — signals "prior week" without blocking use
- Empty DB state: disabled Auto radio + "No projections available yet" message, auto-falls back to Upload CSV

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 10-projection-source-selector*
*Context gathered: 2026-03-25*
