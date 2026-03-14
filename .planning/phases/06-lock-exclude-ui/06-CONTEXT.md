# Phase 6: Lock/Exclude UI - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a collapsible player pool table to `index.html` showing all eligible cards after CSV upload, with per-card lock/exclude checkboxes and a golfer-level lock checkbox. Lock/exclude state submits with the Re-Optimize form. Visually distinguish locked cards in lineup output with a 🔒 icon in a dedicated column.

</domain>

<decisions>
## Implementation Decisions

### Toggle control design
- Two checkboxes per card row: one for "Lock" (card-level) and one for "Exclude"
- Lock/exclude state submits on Re-Optimize form submit — no AJAX/immediate updates needed
- Conflict (checking both Lock and Exclude for the same card) prevented in the browser with JS: checking Lock disables Exclude and vice versa
- Table columns: Lock | Lock Golfer | Exclude | Player | Collection | Salary | Multiplier | Proj Score

### Golfer-level lock UI
- "Lock Golfer" checkbox appears once per player — on the first card row for that player only; subsequent card rows for the same player leave the "Lock Golfer" cell empty
- Cards are not grouped visually — flat table sorted by player name
- Column header: "Lock Golfer"
- Checking "Lock Golfer" forces at least one of the player's cards into a lineup (maps to `locked_golfers` session key)

### Player pool section placement
- Wrapped in a `<details>` element, collapsible like the upload section
- Summary label: "Lock / Exclude Players"
- Collapsed by default when results load
- Page order: Upload section → Lock / Exclude Players → Re-Optimize → Lineups

### Locked card indicator in lineup output
- New "Lock" column added to all lineup result tables (header: "Lock")
- Locked card rows show 🔒 in this column; non-locked rows are blank
- Locked card = card whose composite key (player, salary, multiplier, collection) matches a key in the session's `locked_cards` list

### Claude's Discretion
- Exact form field naming for checkbox inputs (as long as /reoptimize route can parse them)
- Sorting order within the player pool table (by player name, then salary desc)
- CSS styling for the Lock Golfer checkbox cell (e.g., muted for non-first-card rows)
- Whether "Lock" and "Exclude" checkboxes are pre-checked on re-render to reflect current session state

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `<details id="upload-section">` pattern (`index.html`): exact pattern to replicate for the Lock/Exclude Players collapsible section
- `#reoptimize-form` (`index.html`): checkboxes must be inside this form so they submit together with `card_pool` hidden field
- `card_pool_json` hidden field: already carries all card data needed to render checkboxes; `/reoptimize` route will also parse lock/exclude checkbox submissions
- Loading overlay + JS submit listener: reuse as-is, no changes needed
- `style.css` table styles: thead dark green, even-row stripe, tfoot bg — new player pool table inherits these automatically

### Established Patterns
- Vanilla JS only — no framework (existing template has 3-line JS block)
- Lock/exclude session keys: `locked_cards` (list of 4-tuples), `locked_golfers` (list of player name strings), `excluded_cards` (list of 4-tuples), `excluded_players` (list of player name strings)
- Composite card key: `(player, salary, multiplier, collection)` — checkbox `name` or `value` must encode this
- `/reoptimize` POST route in `routes.py` already reads session for `ConstraintSet`; needs to also read checkbox form fields and update session before building `ConstraintSet`

### Integration Points
- `index.html`: player pool `<details>` section renders from `card_pool` (deserialized from `card_pool_json`)
- `/reoptimize` route (`routes.py`): must parse new checkbox form fields → write to session → build `ConstraintSet` → call `optimize()`
- Lineup result tables in `index.html`: add "Lock" column header + `<td>` per row with 🔒 or blank based on whether card key is in `constraints.locked_cards`

</code_context>

<specifics>
## Specific Ideas

- JS conflict prevention: when Lock checkbox is checked → disable the Exclude checkbox for that row, and vice versa. Simple event listeners, no library needed.
- "Lock Golfer" cell appears only on the first card row per player — rows after the first for the same player have an empty `<td>` in that column.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-lock-exclude-ui*
*Context gathered: 2026-03-14*
