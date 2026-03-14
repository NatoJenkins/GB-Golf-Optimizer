# Phase 5: Serialization and Re-Optimize Route - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a Re-Optimize button to the results page that allows users to re-run the optimizer using their current lock/exclude session state without re-uploading CSVs. Requires serializing the card pool (`valid_cards`) into a hidden form field so it survives the request cycle. Lock/exclude UI controls (player pool table, checkboxes) are NOT part of this phase — that's Phase 6. This phase provides the route, the serialization, and the button only.

</domain>

<decisions>
## Implementation Decisions

### Re-Optimize button placement
- Separate `<form>` element, independent from the upload form
- Positioned above the lineup results (first thing user sees after lineups load)
- Always visible after results load — no state check for active locks/excludes
- Does NOT live inside the `<details>` upload section

### Loading behavior
- Reuse the existing full-page "Optimizing…" overlay when Re-Optimize is clicked
- Same overlay text ("Optimizing…") — no distinction from a fresh upload
- No new CSS or JS needed for the loading state

### Card pool lost / session recovery
- If the hidden form field is missing or unparseable (page refresh, server restart, form tampered), show an error: "Session expired — please re-upload your files"
- Render the upload form so user can start over
- Explicit feedback, not a silent redirect

### Re-optimized results presentation
- Visually identical to original optimize results — same tables, same layout
- No badge, label, or count indicator ("Re-optimized with X locks") needed

### Claude's Discretion
- Serialization format for hidden form field (JSON encoding of Card fields)
- Which Card fields to include in serialization (all fields needed to reconstruct the card for the optimizer)
- Route name (`/reoptimize` or handled within `/`)
- Form method and action for the Re-Optimize form

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `loading-overlay` div + JS event listener (`index.html`): already triggers on upload form submit — can be reused for re-optimize form submit with the same or additional JS listener
- `optimize()` (`gbgolf/optimizer/__init__.py`): accepts `valid_cards` list + `constraints` — re-optimize just needs to supply these from deserialized hidden field + session
- `ConstraintSet` (`gbgolf/optimizer/constraints.py`): built from session keys — same construction logic applies for re-optimize
- `index.html` result rendering: the `show_results`, `result`, `validation`, `lock_reset` template vars drive output — re-optimize route can return the same template with same vars

### Established Patterns
- Hidden form field for card pool: decided in Phase 4 (STATE.md) — card objects NOT stored in session; serialized to hidden form field instead
- Composite card key `(player, salary, multiplier, collection)`: used for lock/exclude matching; serialization must preserve these fields
- Pydantic at boundary only: internal Card dataclass used throughout optimizer — deserialization should reconstruct Card objects, not add Pydantic validation
- Lock/exclude state in Flask cookie session: `locked_cards`, `locked_golfers`, `excluded_cards`, `excluded_players` keys

### Integration Points
- New route (e.g., `POST /reoptimize`) reads hidden form field → deserializes cards → reads session for constraints → calls `optimize()` → renders `index.html` with same template vars as the upload route
- `index.html`: needs hidden form field injected into results section, Re-Optimize button form rendered above lineups

</code_context>

<specifics>
## Specific Ideas

No specific UI references — keep it consistent with existing table/form style.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-serialization-and-re-optimize-route*
*Context gathered: 2026-03-14*
