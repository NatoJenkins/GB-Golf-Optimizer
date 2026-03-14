# Phase 6: Lock/Exclude UI - Research

**Researched:** 2026-03-14
**Domain:** Flask/Jinja2 template UI, vanilla JS form controls, HTML `<details>` collapsible, checkbox-based form submission
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Two checkboxes per card row: one for "Lock" (card-level) and one for "Exclude"
- Lock/exclude state submits on Re-Optimize form submit — no AJAX/immediate updates needed
- Conflict (checking both Lock and Exclude for the same card) prevented in the browser with JS: checking Lock disables Exclude and vice versa
- Table columns: Lock | Lock Golfer | Exclude | Player | Collection | Salary | Multiplier | Proj Score
- "Lock Golfer" checkbox appears once per player — on the first card row for that player only; subsequent card rows for the same player leave the "Lock Golfer" cell empty
- Cards are not grouped visually — flat table sorted by player name
- Column header: "Lock Golfer"
- Checking "Lock Golfer" forces at least one of the player's cards into a lineup (maps to `locked_golfers` session key)
- Player pool section wrapped in a `<details>` element, collapsible like the upload section
- Summary label: "Lock / Exclude Players"
- Collapsed by default when results load
- Page order: Upload section → Lock / Exclude Players → Re-Optimize → Lineups
- New "Lock" column added to all lineup result tables (header: "Lock")
- Locked card rows show 🔒 in this column; non-locked rows are blank
- Locked card = card whose composite key (player, salary, multiplier, collection) matches a key in the session's `locked_cards` list

### Claude's Discretion

- Exact form field naming for checkbox inputs (as long as /reoptimize route can parse them)
- Sorting order within the player pool table (by player name, then salary desc)
- CSS styling for the Lock Golfer checkbox cell (e.g., muted for non-first-card rows)
- Whether "Lock" and "Exclude" checkboxes are pre-checked on re-render to reflect current session state

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| UI-01 | User sees their eligible player pool with per-card lock/exclude controls after uploading CSVs | Player pool `<details>` section in `index.html` rendering from `card_pool_json`; checkbox form fields inside `#reoptimize-form`; `/reoptimize` route parses and writes to session |
| UI-03 | Locked cards are visually marked in lineup output confirming constraints took effect | "Lock" column in lineup tables; Jinja2 set of locked_card_keys passed from route; 🔒 icon rendered per matching row |
</phase_requirements>

---

## Summary

Phase 6 is a pure UI addition to an existing, working Flask/Jinja2 application. No new libraries are needed. The work splits cleanly into three sub-concerns: (1) the player pool table rendered in a collapsible `<details>` section inside `#reoptimize-form`, (2) the `/reoptimize` backend route reading checkbox submissions, writing session keys, then building `ConstraintSet`, and (3) the lineup output tables gaining a "Lock" column with a 🔒 indicator.

The existing codebase already has every scaffolding piece in place. `card_pool_json` is already serialized and passed to the template. The four session keys (`locked_cards`, `locked_golfers`, `excluded_cards`, `excluded_players`) are already typed and consumed by `ConstraintSet`. The `<details>` / `<summary>` collapsible pattern is already established by `#upload-section`. Table CSS (`thead` dark green, even-row stripe, `tfoot` bg) inherits automatically.

The only real design decision left to Claude is form field naming. The chosen approach is: card-level lock checkboxes use `name="lock_card"` with `value="{player}|{salary}|{multiplier}|{collection}"` (pipe-delimited composite key); card-level exclude uses `name="exclude_card"` same encoding; golfer-level lock uses `name="lock_golfer"` with `value="{player}"`. The `/reoptimize` route uses `request.form.getlist(...)` to collect all checked values before building the session and `ConstraintSet`.

**Primary recommendation:** Make the player pool `<details>` section and all its checkboxes children of `#reoptimize-form` (which already exists). This means one form submit captures checkboxes + hidden `card_pool` field together — no structural refactoring required.

---

## Standard Stack

### Core (already installed, no changes)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flask | >=3.0 | Route handling, session, `request.form.getlist()` | Already in use |
| Jinja2 | (bundled with Flask) | Template rendering, loop/conditional logic | Already in use |
| Vanilla JS | ES2015+ | Checkbox conflict prevention, event listeners | Established project constraint — no frameworks |

### No New Dependencies

This phase requires zero new `pip install` entries. All functionality is native HTML/Jinja2/JS.

---

## Architecture Patterns

### Recommended Project Structure (no new files required)

```
gbgolf/web/
├── templates/
│   └── index.html        # Player pool <details> section added; lineup tables gain Lock column
├── static/
│   └── style.css         # One new rule: .lock-golfer-empty (muted empty cells)
└── routes.py             # /reoptimize route: parse checkboxes → write session → build ConstraintSet
```

### Pattern 1: Checkbox Encoding with Pipe-Delimited Composite Key

**What:** Each card row has two checkboxes sharing the same composite key encoded as `{player}|{salary}|{multiplier}|{collection}`. The name attribute distinguishes lock vs. exclude. The route collects with `request.form.getlist("lock_card")` etc.

**When to use:** Any time a form submits a variable-length list of string-encoded identifiers. Standard HTML multi-value field pattern — no JS required for collection.

**Example:**
```html
<!-- Card row — inside #reoptimize-form -->
<td>
  <input type="checkbox"
         name="lock_card"
         value="{{ card.player }}|{{ card.salary }}|{{ card.multiplier }}|{{ card.collection }}"
         class="lock-cb"
         {% if (card.player, card.salary, card.multiplier, card.collection) in locked_card_keys %}checked{% endif %}
  />
</td>
<td>
  <!-- Lock Golfer: only rendered on first card row per player -->
  {% if loop.first_for_player %}
  <input type="checkbox"
         name="lock_golfer"
         value="{{ card.player }}"
         class="lock-golfer-cb"
         {% if card.player in locked_golfer_set %}checked{% endif %}
  />
  {% endif %}
</td>
<td>
  <input type="checkbox"
         name="exclude_card"
         value="{{ card.player }}|{{ card.salary }}|{{ card.multiplier }}|{{ card.collection }}"
         class="exclude-cb"
         {% if (card.player, card.salary, card.multiplier, card.collection) in excluded_card_keys %}checked{% endif %}
  />
</td>
```

### Pattern 2: Jinja2 Loop with "First-per-player" Tracking

**What:** Because cards are sorted by player name then salary desc, the template uses a `namespace` variable to track when the player name changes and render the Lock Golfer checkbox only on the first row.

**When to use:** Flat sorted table that needs per-group sentinel rendering without grouping the data server-side.

**Example:**
```jinja2
{% set ns = namespace(prev_player="") %}
{% for card in card_pool %}
<tr>
  <td><input type="checkbox" name="lock_card" value="{{ card.player }}|{{ card.salary }}|{{ card.multiplier }}|{{ card.collection }}" class="lock-cb" /></td>
  <td>
    {% if card.player != ns.prev_player %}
    <input type="checkbox" name="lock_golfer" value="{{ card.player }}" class="lock-golfer-cb" />
    {% set ns.prev_player = card.player %}
    {% endif %}
  </td>
  <td><input type="checkbox" name="exclude_card" value="{{ card.player }}|{{ card.salary }}|{{ card.multiplier }}|{{ card.collection }}" class="exclude-cb" /></td>
  <td>{{ card.player }}</td>
  <td>{{ card.collection }}</td>
  <td>${{ card.salary }}</td>
  <td>{{ card.multiplier }}</td>
  <td>{{ "%.2f"|format(card.projected_score or 0.0) }}</td>
</tr>
{% endfor %}
```

Note: The template receives `card_pool` as a Python list already sorted in the route. The route sorts with `sorted(valid_cards, key=lambda c: (c.player, -c.salary))` before passing to render_template.

### Pattern 3: Vanilla JS Conflict Prevention (Disable-on-Check)

**What:** When a lock checkbox is checked, the exclude checkbox in the same row is disabled (and vice versa). Uses `data-*` attributes to link the pair.

**When to use:** Prevents the lock+exclude conflict that `check_conflicts()` would catch server-side. Better UX to prevent at source.

**Example:**
```javascript
// In the existing <script> block at bottom of index.html
document.querySelectorAll(".lock-cb").forEach(function(lockCb) {
  lockCb.addEventListener("change", function() {
    var row = lockCb.closest("tr");
    var excludeCb = row.querySelector(".exclude-cb");
    if (excludeCb) excludeCb.disabled = lockCb.checked;
  });
});
document.querySelectorAll(".exclude-cb").forEach(function(excludeCb) {
  excludeCb.addEventListener("change", function() {
    var row = excludeCb.closest("tr");
    var lockCb = row.querySelector(".lock-cb");
    if (lockCb) lockCb.disabled = excludeCb.checked;
  });
});
```

Important: A disabled checkbox does NOT submit with the form. This is standard HTML behaviour — disabled inputs are excluded from form data. This means the conflict prevention is both visual AND functional: if Lock is checked, Exclude is disabled and cannot be accidentally submitted.

### Pattern 4: /reoptimize Route — Parse Checkboxes, Write Session, Build ConstraintSet

**What:** The route reads multi-value form fields, parses the pipe-delimited keys back to tuples, writes to session, then builds `ConstraintSet` from the session (same code path as before).

**When to use:** This is the only route change in this phase.

**Example:**
```python
@bp.route("/reoptimize", methods=["POST"])
def reoptimize():
    card_pool_json = request.form.get("card_pool")
    if not card_pool_json:
        return render_template("index.html", error="Session expired — please re-upload your files")

    try:
        valid_cards = _deserialize_cards(card_pool_json)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return render_template("index.html", error="Session expired — please re-upload your files")

    # Parse checkbox submissions
    def _parse_card_keys(raw_list):
        keys = []
        for v in raw_list:
            parts = v.split("|")
            if len(parts) == 4:
                player, salary_s, mult_s, collection = parts
                try:
                    keys.append((player, int(salary_s), float(mult_s), collection))
                except (ValueError, TypeError):
                    pass  # skip malformed
        return keys

    locked_cards = _parse_card_keys(request.form.getlist("lock_card"))
    excluded_cards = _parse_card_keys(request.form.getlist("exclude_card"))
    locked_golfers = [v for v in request.form.getlist("lock_golfer") if v]
    # excluded_players not submitted by Phase 6 UI — preserve from session or empty
    excluded_players = session.get("excluded_players", [])

    # Write parsed constraints to session
    session["locked_cards"] = [list(k) for k in locked_cards]
    session["locked_golfers"] = locked_golfers
    session["excluded_cards"] = [list(k) for k in excluded_cards]
    session["excluded_players"] = excluded_players

    constraints = ConstraintSet(
        locked_cards=locked_cards,
        locked_golfers=locked_golfers,
        excluded_cards=excluded_cards,
        excluded_players=excluded_players,
    )

    result = optimize(valid_cards, current_app.config["CONTESTS"], constraints=constraints)

    return render_template(
        "index.html",
        result=result,
        show_results=True,
        lock_reset=False,
        card_pool_json=card_pool_json,
        card_pool=sorted(valid_cards, key=lambda c: (c.player, -c.salary)),
        locked_card_keys=set(locked_cards),
        locked_golfer_set=set(locked_golfers),
        excluded_card_keys=set(excluded_cards),
    )
```

### Pattern 5: Lineup Table "Lock" Column with Jinja2 Set Lookup

**What:** Pass `locked_card_keys` (a Python set of 4-tuples) to the template. Each lineup card row checks membership.

**Example:**
```jinja2
<thead>
  <tr>
    <th>Lock</th>
    <th>Player</th>
    <th>Collection</th>
    <th>Salary</th>
    <th>Multiplier</th>
    <th>Proj Score</th>
  </tr>
</thead>
<tbody>
  {% for card in lineup.cards %}
  <tr>
    <td>{% if (card.player, card.salary, card.multiplier, card.collection) in locked_card_keys %}🔒{% endif %}</td>
    <td>{{ card.player }}</td>
    ...
  </tr>
  {% endfor %}
</tbody>
```

Note: `locked_card_keys` must be passed from both the `index` route (POST) and the `reoptimize` route. For the `index` POST route it is `set()` since session was just cleared. For `reoptimize` it is built from the parsed form submission.

### Anti-Patterns to Avoid

- **Putting the player pool table outside `#reoptimize-form`:** Checkboxes outside the form don't submit. The player pool `<details>` must be INSIDE the form's opening/closing tags.
- **Using `id()` or index as checkbox value:** Not stable across requests. Composite key is the established pattern.
- **Storing card objects in session:** Already decided against — cookie size limit. Card pool lives in hidden `card_pool` form field only.
- **Using `request.form.get("lock_card")` instead of `request.form.getlist("lock_card")`:** `get()` returns only the first value. Multi-value fields require `getlist()`.
- **Assuming unchecked checkbox sends `"false"`:** HTML checkboxes are absent from form data when unchecked. The absence of a key means unchecked — never submit a "false" value.
- **Jinja2 set membership with list:** Pass Python `set` (not `list`) to the template for `locked_card_keys` — O(1) lookup vs. O(n) per row.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Multi-value form field collection | Custom JS serialization into a single hidden field | `request.form.getlist("field_name")` | Native Flask/Werkzeug, zero code |
| Composite key encoding | JSON or base64 encoding | Pipe-delimited string `{p}\|{s}\|{m}\|{c}` | Simple, human-readable, no extra parsing libs |
| First-row-per-group sentinel | Pre-grouping cards server-side into a dict | Jinja2 `namespace` variable with prev_player tracking | Keeps template logic minimal, data stays flat |
| Lock/exclude conflict check in template | Client-side state machine | Disable the conflicting checkbox in JS `change` handler | Browser form submission handles disabled inputs automatically |

**Key insight:** HTML form submission with `<input type="checkbox">` is the correct primitive here — no JS state management, no AJAX, no hidden field encoding of lock state. Checkboxes either submit or don't; `getlist()` collects all that did.

---

## Common Pitfalls

### Pitfall 1: Float Precision in Composite Key Round-Trip

**What goes wrong:** Multiplier stored as Python `float` (e.g. `1.5`) serializes to JSON as `1.5` and parses back identically. But if it ever stored as `1.4999999...` in the hidden field, the pipe-split value `"1.5"` will not match session tuple `(player, salary, 1.4999..., collection)`.

**Why it happens:** `float("1.5")` is exact in IEEE 754. This is only a risk if multipliers come from arithmetic operations rather than direct CSV parsing. In this codebase multipliers are parsed from CSV strings via `float()` and re-serialized via `json.dumps()` which outputs the shortest representation — so round-trip is stable.

**How to avoid:** Use the multiplier value directly from the deserialized Card object (which was already round-tripped through JSON). Don't recompute it. The composite key tuple must match exactly what `_deserialize_cards` produces.

**Warning signs:** Lock indicator (🔒) never appears even for cards the user locked. Check by printing the key tuple from the route vs. the key tuple from locked_card_keys.

### Pitfall 2: Template Receives `locked_card_keys` as `None` on Initial Upload

**What goes wrong:** After the initial CSV upload (index POST), the template renders with `show_results=True` but no `locked_card_keys` kwarg — causing `{% if ... in locked_card_keys %}` to raise `TypeError`.

**Why it happens:** The index route currently doesn't pass `locked_card_keys`, `card_pool`, etc. Session was just cleared so there are no locked cards, but the template needs a valid empty set.

**How to avoid:** The index route POST must also pass `locked_card_keys=set()`, `locked_golfer_set=set()`, `excluded_card_keys=set()`, and `card_pool=sorted(validation.valid_cards, key=lambda c: (c.player, -c.salary))`.

**Warning signs:** `TypeError: argument of type 'NoneType' is not iterable` in Jinja2 traceback after initial upload.

### Pitfall 3: Player Pool `<details>` Must Be Inside `#reoptimize-form`

**What goes wrong:** Placing the `<details id="player-pool-section">` before the `<form id="reoptimize-form">` means checkboxes are outside the form and do not submit.

**Why it happens:** The page layout in CONTEXT.md says "Lock / Exclude Players → Re-Optimize → Lineups". It's tempting to put the `<details>` section separately and the `<form>` only around the Re-Optimize button. But the form must wrap both.

**How to avoid:** The `<form id="reoptimize-form">` must open BEFORE the player pool `<details>` and close AFTER the Re-Optimize button. The Re-Optimize button is the form's submit trigger. The player pool checkboxes are inside the form.

**Warning signs:** `/reoptimize` receives empty `lock_card` list even when user has checked boxes. Verify with browser dev tools → Network → Form Data.

### Pitfall 4: `disabled` Checkboxes Are Not Submitted

**What goes wrong:** JS disables the Exclude checkbox when Lock is checked. On re-render, the route receives no `exclude_card` submission for that row — correct behaviour. But if the template pre-checks the Exclude box AND it is disabled, the rendered state is inconsistent.

**Why it happens:** If the template pre-checks based on `excluded_card_keys` but that set now contains the conflicted key (shouldn't happen if the route correctly prevents it), the disabled+checked state would confuse users.

**How to avoid:** The route's conflict parsing is the source of truth. A key cannot simultaneously appear in `locked_cards` and `excluded_cards` after the route parses form submissions (because checking Lock disables Exclude, so Exclude checkbox won't submit). Validate this invariant in the `/reoptimize` route: after parsing, assert no key is in both sets (or simply trust JS prevention and let `check_conflicts()` catch edge cases).

### Pitfall 5: `Jinja2` `set` Type for Membership Testing

**What goes wrong:** Passing `locked_card_keys` as a Python `list` to Jinja2 and using `in` operator works correctly but is O(n) per card row. For large card pools this is fine, but it's also easy to accidentally pass a list of lists (from `json.dumps` round-trip) whose tuples won't match.

**Why it happens:** `session["locked_cards"]` stores lists of lists (JSON doesn't have tuples). The route must convert: `locked_cards = [tuple(k) for k in ...]`. Then pass `locked_card_keys = set(locked_cards)` to template.

**How to avoid:** Always convert JSON lists back to tuples immediately after parsing. Wrap in `set()` before passing to template. This is already the pattern in the existing `/reoptimize` route.

---

## Code Examples

### Verified: `request.form.getlist()` for multi-value fields

```python
# Source: Flask documentation / Werkzeug ImmutableMultiDict
# Multiple checkboxes with same name="lock_card" each submit one value.
# getlist() returns all submitted values as a list.
locked_raw = request.form.getlist("lock_card")  # e.g. ["Tiger Woods|11000|1.5|Core", ...]
```

### Verified: Jinja2 `namespace` for loop state tracking

```jinja2
{# Source: Jinja2 docs — scoped variables require namespace() for mutation inside loops #}
{% set ns = namespace(prev_player="") %}
{% for card in card_pool %}
  {% if card.player != ns.prev_player %}
    {# first row for this player #}
    {% set ns.prev_player = card.player %}
  {% endif %}
{% endfor %}
```

### Verified: HTML checkbox — absent when unchecked, present when checked

```html
<!-- Checked: form submits lock_card=Tiger+Woods%7C11000%7C1.5%7CCore -->
<input type="checkbox" name="lock_card" value="Tiger Woods|11000|1.5|Core" checked />

<!-- Unchecked: lock_card key absent entirely from form data -->
<input type="checkbox" name="lock_card" value="Tiger Woods|11000|1.5|Core" />
```

### Verified: HTML `<details>` collapsible section

```html
<!-- Closed by default (no 'open' attribute) -->
<details id="player-pool-section">
  <summary>Lock / Exclude Players</summary>
  <!-- content here -->
</details>

<!-- Open by default -->
<details id="upload-section" open>
  <summary>Upload files</summary>
</details>
```

### Verified: Pipe-delimited key round-trip

```python
# Encoding (template value attribute via Jinja2)
value = f"{card.player}|{card.salary}|{card.multiplier}|{card.collection}"
# e.g. "Tiger Woods|11000|1.5|Core"

# Decoding (route)
parts = value.split("|")  # ["Tiger Woods", "11000", "1.5", "Core"]
key = (parts[0], int(parts[1]), float(parts[2]), parts[3])
# ("Tiger Woods", 11000, 1.5, "Core")
```

Note: Player names may contain spaces but not `|`. Salary and multiplier format in CSV is controlled input; no special characters expected.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Storing card objects in session | Card pool in hidden form field `card_pool_json` | Phase 5 | No cookie size limit risk |
| Session-only constraint reads | Checkbox form submission writes session then reads | Phase 6 | Lock/exclude state flows from UI, not from prior session state |
| No lock column in lineup tables | "Lock" column with 🔒 per locked card row | Phase 6 | UI-03 satisfied |

---

## Open Questions

1. **Pre-checking checkboxes on re-render**
   - What we know: CONTEXT.md marks this as Claude's discretion
   - What's unclear: Whether pre-checking is worth the added template complexity
   - Recommendation: YES — pre-check based on session state. The template already receives `locked_card_keys`, `excluded_card_keys`, `locked_golfer_set`. Pre-checking gives users confirmation their selections were applied. Cost: 3 Jinja2 `checked` conditionals.

2. **What happens to `excluded_players` in Phase 6?**
   - What we know: The player pool table has no "Exclude Golfer" checkbox (only "Exclude" per card). There is no golfer-level exclude in Phase 6 UI.
   - What's unclear: Should `/reoptimize` preserve the prior session `excluded_players` or reset it to `[]`?
   - Recommendation: Preserve from session (`session.get("excluded_players", [])`). The Phase 6 UI doesn't offer a golfer-level exclude control, but the data structure exists. Preserving avoids inadvertently clearing a state that a future phase might set.

3. **Multiplier display in table — float formatting**
   - What we know: The existing lineup table renders `{{ card.multiplier }}` which outputs e.g. `1.5` or `1.0`. The pipe-encoded key uses `{{ card.multiplier }}` for the checkbox value.
   - What's unclear: Will `"1.0"` (from template) round-trip to `float("1.0") == 1.0` correctly? Yes — this is exact IEEE 754.
   - Recommendation: No special formatting needed. Use `{{ card.multiplier }}` directly in checkbox value attribute.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.0+ |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_web.py -x -q` |
| Full suite command | `pytest -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-01 | Player pool `<details>` section rendered after CSV upload | integration | `pytest tests/test_web.py::test_player_pool_section_rendered -x` | Wave 0 |
| UI-01 | Player pool table has correct column headers | integration | `pytest tests/test_web.py::test_player_pool_table_columns -x` | Wave 0 |
| UI-01 | Lock/Exclude checkboxes present per row inside reoptimize-form | integration | `pytest tests/test_web.py::test_lock_exclude_checkboxes_in_form -x` | Wave 0 |
| UI-01 | Lock Golfer checkbox appears once per player (first row only) | integration | `pytest tests/test_web.py::test_lock_golfer_first_row_only -x` | Wave 0 |
| UI-01 | /reoptimize parses lock_card form fields and writes session | integration | `pytest tests/test_web.py::test_reoptimize_parses_lock_checkboxes -x` | Wave 0 |
| UI-01 | /reoptimize parses exclude_card form fields and writes session | integration | `pytest tests/test_web.py::test_reoptimize_parses_exclude_checkboxes -x` | Wave 0 |
| UI-01 | /reoptimize parses lock_golfer form fields and writes session | integration | `pytest tests/test_web.py::test_reoptimize_parses_lock_golfer -x` | Wave 0 |
| UI-03 | Lock column header present in lineup tables after reoptimize | integration | `pytest tests/test_web.py::test_lineup_lock_column_header -x` | Wave 0 |
| UI-03 | Locked card row shows lock icon in lineup output | integration | `pytest tests/test_web.py::test_locked_card_shows_lock_icon -x` | Wave 0 |
| UI-03 | Non-locked card row shows blank in Lock column | integration | `pytest tests/test_web.py::test_nonlocked_card_blank_lock_column -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_web.py -x -q`
- **Per wave merge:** `pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_web.py` — add ~10 new test functions (listed above) covering UI-01 and UI-03; existing file exists but lacks Phase 6 tests
- [ ] No new fixture or conftest changes needed — existing `client` fixture is sufficient

*(No framework install needed — pytest already configured in pyproject.toml)*

---

## Sources

### Primary (HIGH confidence)

- Direct code inspection of `gbgolf/web/routes.py` — existing serialize/deserialize pattern, session key names, ConstraintSet construction
- Direct code inspection of `gbgolf/web/templates/index.html` — `<details>` pattern, `#reoptimize-form`, card_pool_json hidden field, JS event listeners
- Direct code inspection of `gbgolf/web/static/style.css` — inherited table styles, `#upload-section` pattern
- Direct code inspection of `gbgolf/optimizer/constraints.py` — ConstraintSet fields, CardKey definition
- `pyproject.toml` — pytest 8.0+, Flask 3.0+, testpaths configuration
- HTML specification (standard) — checkbox absent-when-unchecked behaviour; `disabled` attribute excludes from form submission

### Secondary (MEDIUM confidence)

- Flask documentation — `request.form.getlist()` for multi-value fields
- Jinja2 documentation — `namespace()` scoped variable for loop mutation

### Tertiary (LOW confidence)

None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries; all existing
- Architecture: HIGH — patterns derived directly from existing codebase
- Pitfalls: HIGH — derived from HTML/Flask spec behaviour and code inspection
- Test map: HIGH — test names are descriptive and map 1:1 to phase requirements

**Research date:** 2026-03-14
**Valid until:** 2026-06-14 (stable stack — Flask 3.x, HTML5, no fast-moving dependencies)
