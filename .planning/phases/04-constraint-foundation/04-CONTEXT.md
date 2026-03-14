# Phase 4: Constraint Foundation - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Backend engine layer only. Deliver: stable card identity, ILP lock/exclude constraints, pre-solve diagnostics, and session reset on new CSV upload. No UI changes — the player pool table, lock/exclude controls, and Re-Optimize button are Phase 6. Phase 4 must be callable from the existing `/` route via Flask session state so Phase 5 and 6 can build on it without rework.

</domain>

<decisions>
## Implementation Decisions

### Golfer-lock semantics
- Golfer lock (by player name) = "at least one lineup, any contest" — the optimizer must place one of the player's cards in at least one lineup across Tips and Intermediate Tee combined
- Card lock (specific card by composite key) = forced into the first lineup where it fits salary and collection constraints
- No per-contest targeting — all locks apply globally across both contests
- If a locked golfer has only one card and it's consumed in lineup 1, lineup 2 builds normally with no error (the "at least one" requirement was already satisfied)

### Infeasibility diagnostics (LOCK-03)
- Pre-solve checks run in Python before calling PuLP — fast O(n) checks, no solver overhead
- Messages include the specific numbers, not just error type: e.g., "Locked cards total $42,000. Salary cap is $64,000. Remaining $22,000 for 2 slots, but minimum possible is $25,000."
- Two violation types trigger a pre-solve error:
  1. Salary cap exceeded: locked card salary sum > contest salary_max
  2. Collection limit exceeded: locked cards in a collection exceed the limit for that collection
- When a pre-solve error is found: stop entirely, return the error, do not attempt to build any lineups. User fixes locks, then re-optimizes.

### Session reset (UI-04)
- Any POST with file uploads (roster + projections) clears all lock and exclude state unconditionally — simple and predictable rule
- After clearing, show a visible banner on the results page: "Locks and excludes reset for new upload"
- No fingerprint/hash comparison — always reset on upload

### Lock/exclude scope
- Card exclude: card is removed from all lineups across both contests
- Golfer exclude: all cards for that player are removed from all lineups across both contests
- No per-contest targeting for excludes
- Conflict detection (LOCK-04): if a locked card belongs to an excluded player (or a locked player is also in the excluded set), return a conflict error before any solve attempt

### Stable card key
- Composite key: `(player, salary, multiplier, collection)` — already decided (STATE.md)
- Never use Python `id()` for lock/exclude matching
- Session stores lock/exclude state as lists of these tuples (JSON-serializable for Flask cookie session)

### Claude's Discretion
- Internal structure of the ConstraintSet (flat params vs. dataclass with validate() method)
- Error return type for pre-solve failures (exception vs. result object)
- How to thread constraint state from session into the optimize() call signature

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Card` dataclass (`gbgolf/data/models.py`): player, salary, multiplier, collection fields are the stable key fields — no changes needed to Card itself
- `_solve_one_lineup()` (`gbgolf/optimizer/engine.py`): binary ILP, takes `cards` + `config` — will accept additional lock/exclude params; returns None on infeasibility
- `optimize()` (`gbgolf/optimizer/__init__.py`): sequential multi-lineup loop, uses `id(c)` for `used_card_ids` — must switch to stable composite key
- `OptimizationResult.infeasibility_notices` (`gbgolf/optimizer/__init__.py`): already a list of strings — pre-solve diagnostics can slot in here or as a separate field
- `routes.py` single `/` POST handler: already handles file uploads and passes to optimize() — lock/exclude state read from session here, session cleared on upload here

### Established Patterns
- Validation done at boundary (Pydantic for external JSON, dataclasses internally) — constraint validation follows same pattern: check at route boundary before calling engine
- `id(c)` used for cross-lineup deduplication in optimize() — this needs to migrate to composite key tuples for Phase 4

### Integration Points
- `routes.py` → `optimize()`: lock/exclude params must be added to this call
- Flask session: lock/exclude state lives here; cleared on any POST with uploaded files
- `_solve_one_lineup()`: ILP constraint additions (`x[i] == 1` for card locks, `lpSum >= 1` for golfer locks, pre-filter for excludes)

</code_context>

<specifics>
## Specific Ideas

No specific references — standard ILP constraint patterns apply. Refer to PITFALLS.md for full checklist of edge cases already researched.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-constraint-foundation*
*Context gathered: 2026-03-14*
