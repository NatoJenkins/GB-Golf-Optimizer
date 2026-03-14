# Phase 7: Polish - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Add active constraint count display and clear-all button tests (UI-05, UI-06), plus sortable columns on the player pool table. All changes are client-side JS and Jinja2 template only — no backend or session logic changes. Phase 7 is the final phase of v1.1.

</domain>

<decisions>
## Implementation Decisions

### Active constraint count display (UI-06)
- Live JS counter — updates instantly as checkboxes are toggled, no server round-trip
- Placement: above the Re-Optimize button, outside the collapsible player pool section
- Format: `Locks: 2 | Excludes: 1`
- Lock Golfer checkboxes count as locks (not tracked separately)
- Hidden completely when count is 0 — no "No active constraints" message, just invisible
- Count also resets to 0 visually when Clear All is clicked (JS updates it immediately)

### Clear-all button (UI-05)
- Button already exists in template from Phase 6 work
- Tests needed: HTML presence tests only (server-side) — verify button renders when results are shown
- Behavior (unchecking, count reset) is pure JS — not tested via Python tests

### Sortable player pool columns
- All columns are sortable: Lock, Lock Golfer, Exclude, Player, Collection, Salary, Multiplier, Proj Score
- Default sort on page load: Player name A-Z (matches current server-side order)
- Click once: descending; click again: ascending; toggle on each click
- Sort indicator: ▲ for ascending, ▼ for descending in the column header next to the label
- Checkbox column sort order: checked rows first when descending, unchecked first when ascending
- Sort state resets to default (Player A-Z) on Re-Optimize re-render — not persisted through form submission
- Pure JS implementation — no libraries, consistent with existing vanilla JS in the template

### Test scope for count display (UI-06)
- Server-side tests verify the count element is present in the HTML response when results are shown
- Count value is computed by JS — not asserted in Python tests

### Claude's Discretion
- CSS styling for the count display (color, font weight, spacing above Re-Optimize)
- Exact HTML element for count display (span, div, p)
- CSS class name for the count element
- JS implementation approach for sort (e.g., data attributes vs. cell text parsing)
- Arrow styling (Unicode ▲▼ vs CSS pseudo-elements)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `clearAllCheckboxes()` JS function (`index.html` lines 225–230): already unchecks and re-enables all `.lock-cb`, `.lock-golfer-cb`, `.exclude-cb` — extend to also update count display
- Clear All button (`index.html` line 61): already exists with `onclick="clearAllCheckboxes()"` — no HTML changes needed for UI-05
- `.lock-cb`, `.lock-golfer-cb`, `.exclude-cb` CSS classes: already applied to all checkboxes — count JS can query these directly
- Existing `change` event listeners on lock/exclude checkboxes (lines 211–224): add count update call here

### Established Patterns
- Vanilla JS only — no framework, no libraries (3 existing `document.querySelectorAll` blocks)
- Table structure: `<thead>` with `<th>` headers, `<tbody>` with `<tr>` rows — standard DOM sort pattern applies
- `#reoptimize-form` wraps the entire player pool section — sort operates on `<tbody>` rows inside this form; checkbox values are unaffected by row reorder

### Integration Points
- Count display element: new element rendered above `<button type="submit">Re-Optimize</button>` (line 121)
- Sort headers: click handlers added to all `<th>` elements in the player pool `<table>` (lines 63–73)
- `clearAllCheckboxes()`: extend to reset count display to hidden state

</code_context>

<specifics>
## Specific Ideas

- Count display hidden (not just zero) when no active constraints — cleaner than showing zeros
- Checked rows float to top when sorting a checkbox column (descending = checked first)

</specifics>

<deferred>
## Deferred Ideas

- Site-wide visual design (color scheme, typography, layout aesthetics) — future milestone (v1.2 or dedicated design phase). Best tackled after v1.1 feature set is complete so the full UI surface is styled at once, not piecemeal.

</deferred>

---

*Phase: 07-polish*
*Context gathered: 2026-03-14*
