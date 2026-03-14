# Phase 4: Constraint Foundation - Research

**Researched:** 2026-03-14
**Domain:** PuLP ILP constraint addition, Flask session, Python pre-solve diagnostics
**Confidence:** HIGH — all findings verified against existing codebase; no external library changes needed

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Phase boundary:** Backend engine layer only. No UI changes. Phase 4 must be callable from the existing `/` route via Flask session state so Phase 5 and 6 can build on it without rework.

**Golfer-lock semantics:**
- Golfer lock (by player name) = "at least one lineup, any contest" — optimizer places one of the player's cards in at least one lineup across Tips and Intermediate Tee combined
- Card lock (specific card by composite key) = forced into the first lineup where it fits salary and collection constraints
- No per-contest targeting — all locks apply globally across both contests
- If a locked golfer has only one card and it's consumed in lineup 1, lineup 2 builds normally with no error

**Infeasibility diagnostics (LOCK-03):**
- Pre-solve checks run in Python before calling PuLP — O(n), no solver overhead
- Messages include specific numbers: e.g., "Locked cards total $42,000. Salary cap is $64,000. Remaining $22,000 for 2 slots, but minimum possible is $25,000."
- Two violation types trigger a pre-solve error:
  1. Salary cap exceeded: locked card salary sum > contest salary_max
  2. Collection limit exceeded: locked cards in a collection exceed the limit for that collection
- When a pre-solve error is found: stop entirely, return the error, do not build any lineups. User fixes locks, then re-optimizes.

**Session reset (UI-04):**
- Any POST with file uploads (roster + projections) clears all lock and exclude state unconditionally
- After clearing, show a visible banner on the results page: "Locks and excludes reset for new upload"
- No fingerprint/hash comparison — always reset on upload

**Lock/exclude scope:**
- Card exclude: card removed from all lineups across both contests
- Golfer exclude: all cards for that player removed from all lineups across both contests
- No per-contest targeting for excludes
- Conflict detection (LOCK-04): if a locked card belongs to an excluded player (or a locked player is also in the excluded set), return a conflict error before any solve attempt

**Stable card key:**
- Composite key: `(player, salary, multiplier, collection)` — already decided
- Never use Python `id()` for lock/exclude matching
- Session stores lock/exclude state as lists of these tuples (JSON-serializable for Flask cookie session)

### Claude's Discretion

- Internal structure of the ConstraintSet (flat params vs. dataclass with validate() method)
- Error return type for pre-solve failures (exception vs. result object)
- How to thread constraint state from session into the optimize() call signature

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LOCK-01 | User can lock a specific card (player + multiplier) to force it into the optimizer | ILP equality constraint `x[i] == 1` on matched card index; pre-filter excluded cards before building `x` |
| LOCK-02 | User can lock a golfer by name to force at least one of their cards into a lineup | ILP `lpSum(x[i] for i in player_indices) >= 1` for a single targeted lineup; golfer-lock only needs to fire once globally |
| LOCK-03 | App shows informative error when locked cards make salary or collection constraints infeasible before running the optimizer | Pure Python O(n) pre-solve pass: sum locked salaries vs. salary_max, count locked cards per collection vs. collection_limits |
| LOCK-04 | App warns user when a lock and exclude conflict on the same player or card | Set-intersection check on locked keys vs. excluded keys before any solve attempt |
| EXCL-01 | User can exclude a specific card from all lineups in this session | Pre-filter: remove cards whose composite key matches excluded card keys from `available` list before each `_solve_one_lineup` call |
| EXCL-02 | User can exclude a golfer by name, removing all their cards from all lineups | Pre-filter: remove all cards whose `player` field matches excluded player names |
| UI-04 | Lock/exclude state resets automatically when new CSVs are uploaded | Flask route: detect file-upload POST, call `session.pop()` or `session.clear()` on lock/exclude keys before processing |
</phase_requirements>

---

## Summary

Phase 4 adds lock and exclude constraints to the optimizer without introducing any new dependencies. The entire implementation lives in three layers: (1) a `ConstraintSet` data structure that holds lock/exclude state, (2) pre-solve diagnostic checks in pure Python, and (3) PuLP constraint additions injected into `_solve_one_lineup`. The Flask session stores lock/exclude identifiers as JSON-serializable tuples and clears them unconditionally on any file-upload POST.

The codebase is already well-structured for this extension. `_solve_one_lineup` accepts `cards + config` and returns `None` on infeasibility — adding lock/exclude params follows the exact same pattern. The one internal migration required is replacing `id(c)` with composite key tuples in `optimize()` for cross-lineup deduplication.

The primary design decision left to Claude's discretion (ConstraintSet structure and error return type) resolves cleanly using a dataclass with a `validate()` method returning a typed result, avoiding bare exceptions in the happy path while keeping the API testable.

**Primary recommendation:** Add `ConstraintSet` dataclass to `gbgolf/optimizer/constraints.py`, update `optimize()` signature to accept it, implement pre-solve checks and ILP additions inline — no new pip packages.

---

## Standard Stack

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PuLP | >=3.3.0 | ILP constraint addition | Already the optimizer engine; lock/exclude are just additional `lpSum` constraints |
| Flask | >=3.0 | Cookie session for lock/exclude state | Already the web layer; built-in session is sufficient (fits under 4KB) |
| Python dataclasses | stdlib | ConstraintSet structure | Already the established internal pattern (Card, ContestConfig, OptimizationResult) |
| pytest | >=8.0 | Test framework | Already configured in pyproject.toml |

### No New Dependencies
Everything required is already installed. Lock/exclude is pure data-structure and ILP-constraint work.

---

## Architecture Patterns

### Recommended Module Structure

```
gbgolf/
├── optimizer/
│   ├── __init__.py          # optimize() — add constraints param; fix id() -> composite key
│   ├── engine.py            # _solve_one_lineup() — add lock/exclude constraint params
│   └── constraints.py       # NEW: ConstraintSet dataclass + pre-solve diagnostics
├── web/
│   └── routes.py            # Add session read/clear; pass ConstraintSet to optimize()
tests/
├── test_optimizer.py        # Existing; update id()-based tests to composite key
└── test_constraints.py      # NEW: unit tests for ConstraintSet and pre-solve checks
```

### Pattern 1: ConstraintSet Dataclass

**What:** A dataclass holding lock/exclude state with a `validate()` method that returns diagnostic errors before the solver is called.

**When to use:** Called by `routes.py` after reading session, before calling `optimize()`.

```python
# gbgolf/optimizer/constraints.py
from dataclasses import dataclass, field

CardKey = tuple  # (player: str, salary: int, multiplier: float, collection: str)

@dataclass
class ConstraintSet:
    locked_cards: list[CardKey] = field(default_factory=list)    # LOCK-01
    locked_golfers: list[str] = field(default_factory=list)      # LOCK-02
    excluded_cards: list[CardKey] = field(default_factory=list)  # EXCL-01
    excluded_players: list[str] = field(default_factory=list)    # EXCL-02

    def card_key(self, card) -> CardKey:
        return (card.player, card.salary, card.multiplier, card.collection)
```

**Why dataclass over flat params:** Keeps the `optimize()` signature stable as constraints grow (v1.2 adds exposure limits); validate() method keeps diagnostic logic co-located with the data.

### Pattern 2: Pre-Solve Diagnostics

**What:** Pure Python checks on locked cards before calling PuLP. Run once per contest per lineup slot (only the first lineup slot matters for salary/collection checks since locked cards are forced into lineup 1).

**When to use:** Called inside `optimize()` before the lineup loop begins, once per contest config.

```python
# gbgolf/optimizer/constraints.py
@dataclass
class PreSolveError:
    message: str

def check_feasibility(
    constraints: ConstraintSet,
    valid_cards: list,
    config: ContestConfig,
) -> PreSolveError | None:
    """Returns PreSolveError if locked cards violate salary or collection limits.
    Returns None if feasible (no guaranteed infeasibility detected).
    """
    # Build lookup: composite key -> Card
    card_map = {(c.player, c.salary, c.multiplier, c.collection): c for c in valid_cards}

    locked = [card_map[k] for k in constraints.locked_cards if k in card_map]

    # Check 1: Salary cap
    locked_salary = sum(c.salary for c in locked)
    if locked_salary > config.salary_max:
        return PreSolveError(
            f"Locked cards total ${locked_salary:,}. Salary cap is ${config.salary_max:,}. "
            f"Remove locked cards to proceed."
        )

    # Check 2: Collection limits
    from collections import Counter
    collection_counts = Counter(c.collection for c in locked)
    for coll, count in collection_counts.items():
        limit = config.collection_limits.get(coll)
        if limit is not None and count > limit:
            return PreSolveError(
                f"Locked cards include {count} '{coll}' cards but the limit is {limit}. "
                f"Remove {count - limit} locked '{coll}' card(s) to proceed."
            )

    return None
```

### Pattern 3: Conflict Detection (LOCK-04)

**What:** Set-intersection check between locked card keys / locked golfer names and excluded card keys / excluded player names. Runs before pre-solve feasibility check.

```python
def check_conflicts(constraints: ConstraintSet) -> PreSolveError | None:
    """Returns error if any lock target is also an exclude target."""
    locked_card_set = set(constraints.locked_cards)
    excluded_card_set = set(constraints.excluded_cards)
    card_conflicts = locked_card_set & excluded_card_set
    if card_conflicts:
        names = [k[0] for k in card_conflicts]
        return PreSolveError(
            f"Conflict: {', '.join(names)} card(s) are both locked and excluded. "
            f"Remove the conflicting lock or exclude to proceed."
        )

    locked_golfer_set = set(constraints.locked_golfers)
    excluded_player_set = set(constraints.excluded_players)
    golfer_conflicts = locked_golfer_set & excluded_player_set
    if golfer_conflicts:
        return PreSolveError(
            f"Conflict: {', '.join(golfer_conflicts)} is both locked and excluded. "
            f"Remove the conflicting lock or exclude to proceed."
        )

    return None
```

### Pattern 4: ILP Constraint Injection in `_solve_one_lineup`

**What:** Add lock and exclude constraints to the existing PuLP problem. Excludes are handled by pre-filtering `cards` before passing to the function. Card locks add `x[i] == 1`. Golfer locks add `lpSum >= 1`.

**When to use:** Only inject card-lock and golfer-lock constraints when the relevant lock applies to the current lineup (golfer lock fires only once — track whether it has fired via a set passed through the optimize loop).

```python
# In engine.py — updated _solve_one_lineup signature
def _solve_one_lineup(
    cards: list,
    config: ContestConfig,
    locked_card_keys: set | None = None,    # fire in every lineup (LOCK-01)
    locked_golfer_names: set | None = None,  # fire only once globally (LOCK-02)
) -> list | None:
    ...
    # Card lock: x[i] == 1 for each locked card present in this pool
    if locked_card_keys:
        for i, c in enumerate(cards):
            key = (c.player, c.salary, c.multiplier, c.collection)
            if key in locked_card_keys:
                prob += x[i] == 1

    # Golfer lock: at least one card for this player selected
    if locked_golfer_names:
        for golfer in locked_golfer_names:
            player_indices = [i for i, c in enumerate(cards) if c.player == golfer]
            if player_indices:
                prob += pulp.lpSum(x[i] for i in player_indices) >= 1
```

### Pattern 5: Composite Key Migration in `optimize()`

**What:** Replace `id(c)` with composite key tuples for cross-lineup card deduplication. This is required before lock/exclude can work correctly across requests.

```python
# Before (Phase 3):
used_card_ids: set = set()
available = [c for c in valid_cards if id(c) not in used_card_ids]
used_card_ids.add(id(card))

# After (Phase 4):
used_card_keys: set = set()
def _card_key(c): return (c.player, c.salary, c.multiplier, c.collection)
available = [c for c in valid_cards if _card_key(c) not in used_card_keys]
used_card_keys.add(_card_key(card))
```

### Pattern 6: Flask Session Integration

**What:** Read lock/exclude from Flask session in `routes.py`, build ConstraintSet, clear on upload.

```python
# In routes.py — POST handler
from flask import session
from gbgolf.optimizer.constraints import ConstraintSet, check_conflicts, check_feasibility

# On file upload: clear lock/exclude state unconditionally (UI-04)
if request.files.get("roster") or request.files.get("projections"):
    session.pop("locked_cards", None)
    session.pop("locked_golfers", None)
    session.pop("excluded_cards", None)
    session.pop("excluded_players", None)
    lock_reset = True  # pass to template for banner

# Build ConstraintSet from session (lists of JSON-serializable tuples/strings)
constraints = ConstraintSet(
    locked_cards=[tuple(k) for k in session.get("locked_cards", [])],
    locked_golfers=session.get("locked_golfers", []),
    excluded_cards=[tuple(k) for k in session.get("excluded_cards", [])],
    excluded_players=session.get("excluded_players", []),
)
```

### Pattern 7: Golfer-Lock "Fire Once" Tracking

**What:** The golfer lock ("at least one lineup") must fire in exactly one lineup. Track which golfers have been satisfied in the optimize loop.

```python
# In optimize() — golfer lock fires once globally
unsatisfied_golfer_locks = set(constraints.locked_golfers)

for config in contests:
    for entry_num in range(config.max_entries):
        # Only inject golfer locks not yet satisfied
        result = _solve_one_lineup(
            available, config,
            locked_card_keys=set(constraints.locked_cards),
            locked_golfer_names=unsatisfied_golfer_locks,
        )
        if result is not None:
            # Mark golfer locks as satisfied if their player appears in this lineup
            for card in result:
                unsatisfied_golfer_locks.discard(card.player)
```

### Anti-Patterns to Avoid

- **`id(c)` for card identity:** Python object identity breaks across requests (different object, same card). Always use composite key `(player, salary, multiplier, collection)`.
- **Storing Card objects in Flask session:** Card objects are not JSON-serializable. Store only the composite key tuple.
- **Running PuLP to detect pre-solve failures:** Pre-solve checks in pure Python are O(n) and deterministic. Do not call the solver to detect locked-salary > salary_max.
- **Injecting golfer-lock constraint in every lineup:** Golfer lock semantics are "at least one lineup globally." If injected every lineup iteration, the solver may fail on lineup 2+ when the golfer has only one card (already consumed). Track satisfaction and stop injecting once satisfied.
- **Per-contest lock/exclude targeting:** All locks and excludes apply globally across both contests per the locked decision. No contest-specific filtering logic.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ILP constraint for "force this card in" | Custom pre-filter or post-filter | PuLP `x[i] == 1` equality constraint | PuLP handles solver interactions; pre-filter would change objective landscape |
| ILP constraint for "at least one player" | Loop logic outside solver | PuLP `lpSum >= 1` constraint | Solver handles infeasibility correctly; external logic cannot |
| Session serialization | Custom pickle/encoding | Flask built-in session (JSON cookie) | Already decided; tuples serialize to JSON lists natively via `json.dumps` |
| Conflict detection algorithm | Complex graph traversal | Set intersection (`locked & excluded`) | The relationship is flat (no transitive dependencies); O(1) set ops suffice |

**Key insight:** PuLP constraints are cheap to add and the solver handles the combinatorics. Pre-solve checks catch only the trivially infeasible cases (arithmetic violations); the solver catches everything else.

---

## Common Pitfalls

### Pitfall 1: Golfer Lock Fires in Every Lineup, Causes Lineup 2+ Infeasibility
**What goes wrong:** If `locked_golfer_names` is passed unchanged to every `_solve_one_lineup` call, lineup 2 fails when the golfer's only card was used in lineup 1 (already in `used_card_keys`, filtered from `available`).
**Why it happens:** The "at least one lineup" semantic is implemented at the `optimize()` loop level, not inside `_solve_one_lineup`.
**How to avoid:** Track `unsatisfied_golfer_locks` in `optimize()`; remove a golfer from the set once their card appears in any result; pass only unsatisfied locks to subsequent calls.
**Warning signs:** Test where a golfer has exactly one card fails on lineup 2 with infeasibility notice.

### Pitfall 2: Card Lock Applied to All Lineups
**What goes wrong:** A card lock forces the card into lineup 1. But the card is then consumed (added to `used_card_keys`) and filtered from `available` in lineup 2. If the lock constraint is injected again in lineup 2, the solver finds no card matching the key and the constraint `x[i] == 1` has no variable — or the card simply isn't in the pool.
**Why it happens:** Card lock semantics say "forced into the first lineup where it fits" (CONTEXT.md). It is not a "every lineup" constraint.
**How to avoid:** Once a locked card key appears in `used_card_keys`, remove it from the active locked_card_keys set passed to subsequent calls.
**Warning signs:** Lineup 2 infeasibility notices when a locked card was successfully placed in lineup 1.

### Pitfall 3: Flask Session Stores Tuples as Lists
**What goes wrong:** `session["locked_cards"] = [(player, salary, multiplier, collection)]` — Flask JSON-encodes tuples as lists. On retrieval, `session.get("locked_cards")` returns `[[player, salary, multiplier, collection]]`. Comparing a tuple key `(player, salary, multiplier, collection)` to a list `[player, salary, multiplier, collection]` fails silently.
**Why it happens:** JSON has no tuple type; Flask uses `json.dumps` for cookie session serialization.
**How to avoid:** Always cast back: `[tuple(k) for k in session.get("locked_cards", [])]`. Do this in one place (ConstraintSet construction in routes.py).
**Warning signs:** Lock constraints have no effect despite being in session; no error raised.

### Pitfall 4: Pre-Solve Check Ignores Excluded Cards in Locked Set
**What goes wrong:** Pre-solve salary check sums all locked cards including ones the user also excluded. An excluded locked card has already triggered a conflict error, so this is only reachable if conflict detection is skipped.
**Why it happens:** Check ordering error — conflict detection must run before feasibility check.
**How to avoid:** Always run `check_conflicts()` before `check_feasibility()`. Return early on any error.

### Pitfall 5: Composite Key Float Comparison for Multiplier
**What goes wrong:** `multiplier` is a `float` on the `Card` dataclass. Float comparison in composite keys can fail for values computed from arithmetic (e.g., `1.1 + 0.1 != 1.2` in IEEE 754). If multipliers are re-computed rather than read directly from the Card field, key matching fails.
**Why it happens:** Float arithmetic is not exact. Composite key comparison requires exact equality.
**How to avoid:** Always build composite keys directly from `card.multiplier` (the stored field value, parsed once from CSV). Never recompute multiplier from other fields. The CSV parser already handles this correctly.
**Warning signs:** Lock constraint has no effect for cards with non-integer multipliers (1.1, 1.2, etc.).

### Pitfall 6: `id()`-Based Tests in test_optimizer.py Break After Migration
**What goes wrong:** `test_no_card_reuse_across_contests` and `test_card_uniqueness_all_lineups` use `id(card)` directly. After migrating `optimize()` to composite keys, these tests still pass (since in-memory objects still have unique ids per request). But if composite key logic has a bug, the tests won't catch it.
**Why it happens:** Tests were written for the `id()` era.
**How to avoid:** Update affected tests to verify composite key uniqueness in addition to (or instead of) `id()` uniqueness.

---

## Code Examples

Verified patterns from existing codebase:

### Existing ILP Equality/Inequality Constraint Syntax (PuLP)
```python
# Source: gbgolf/optimizer/engine.py (existing code)
# Equality: exactly N cards
prob += pulp.lpSum(x[i] for i in range(n)) == config.roster_size

# Inequality: at most N from collection
prob += pulp.lpSum(x[i] for i in eligible) <= limit

# New for Phase 4 — card lock (equality on single variable)
prob += x[i] == 1

# New for Phase 4 — golfer lock (sum >= 1)
prob += pulp.lpSum(x[i] for i in player_indices) >= 1
```

### Composite Key Construction
```python
# Source: gbgolf/data/models.py (Card fields — verified)
def card_key(c) -> tuple:
    return (c.player, c.salary, c.multiplier, c.collection)
    # Types: str, int, float, str — all JSON-serializable as primitives
```

### Flask Session Access Pattern
```python
# Source: gbgolf/web/__init__.py + routes.py patterns
from flask import session

# Write (storing as list-of-lists since JSON has no tuples):
session["locked_cards"] = [list(k) for k in locked_keys]

# Read (cast back to tuples):
locked_cards = [tuple(k) for k in session.get("locked_cards", [])]
```

### OptimizationResult with Pre-Solve Error
```python
# Source: gbgolf/optimizer/__init__.py (existing OptimizationResult)
# Pre-solve error approach: return early with empty lineups + error in notices
if error := check_conflicts(constraints):
    return OptimizationResult(
        lineups={c.name: [] for c in contests},
        unused_cards=valid_cards,
        infeasibility_notices=[error.message],
    )
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `id(c)` for card deduplication | Composite key `(player, salary, multiplier, collection)` | Phase 4 migration | Enables lock/exclude matching across request boundaries |
| No lock/exclude params on `optimize()` | `optimize(valid_cards, contests, constraints)` | Phase 4 | Stable API for Phase 5 and 6 to build on |

---

## Open Questions

1. **Card lock: does it fire in all lineups or only the first?**
   - What we know: CONTEXT.md says "forced into the first lineup where it fits salary and collection constraints." This implies card-lock fires once.
   - What's confirmed: Card is consumed after lineup 1 (`used_card_keys`), so it cannot appear in lineup 2 regardless. The only question is whether to re-inject the constraint in subsequent lineups (which would cause infeasibility if card is gone).
   - Recommendation: Do NOT inject card-lock constraint after the card has been consumed. Remove from active locked set once placed.

2. **Error return type for pre-solve failures**
   - What we know: Left to Claude's discretion. `OptimizationResult.infeasibility_notices` is an existing `list[str]`.
   - Recommendation: Use a `PreSolveError` dataclass (not an exception) for internal flow, then slot the `.message` into `infeasibility_notices` when returning `OptimizationResult`. This keeps the route handler uniform — it always receives `OptimizationResult` and checks `infeasibility_notices` for problems.

3. **ConstraintSet internal structure**
   - Left to Claude's discretion.
   - Recommendation: Dataclass with explicit fields (not flat params) because Phase 5/6 will pass the same object through Flask route → session → optimize(). Dataclass is explicit, testable, and extensible.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_constraints.py -x -q` |
| Full suite command | `pytest -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LOCK-01 | Card lock places exact card in lineup | unit | `pytest tests/test_constraints.py::test_card_lock_places_card -x` | ❌ Wave 0 |
| LOCK-01 | Card lock with no matching card in pool is silently skipped | unit | `pytest tests/test_constraints.py::test_card_lock_missing_card -x` | ❌ Wave 0 |
| LOCK-02 | Golfer lock places one of player's cards in at least one lineup | unit | `pytest tests/test_constraints.py::test_golfer_lock_satisfied -x` | ❌ Wave 0 |
| LOCK-02 | Golfer lock does not fire in lineup 2 if already satisfied | unit | `pytest tests/test_constraints.py::test_golfer_lock_fires_once -x` | ❌ Wave 0 |
| LOCK-03 | Pre-solve detects locked salary > salary_max | unit | `pytest tests/test_constraints.py::test_presolve_salary_exceeded -x` | ❌ Wave 0 |
| LOCK-03 | Pre-solve detects locked collection count > limit | unit | `pytest tests/test_constraints.py::test_presolve_collection_exceeded -x` | ❌ Wave 0 |
| LOCK-03 | Pre-solve message contains specific numbers | unit | `pytest tests/test_constraints.py::test_presolve_message_content -x` | ❌ Wave 0 |
| LOCK-04 | Conflict: locked card also excluded returns error | unit | `pytest tests/test_constraints.py::test_conflict_card_lock_exclude -x` | ❌ Wave 0 |
| LOCK-04 | Conflict: locked golfer also excluded returns error | unit | `pytest tests/test_constraints.py::test_conflict_golfer_lock_exclude -x` | ❌ Wave 0 |
| EXCL-01 | Excluded card does not appear in any lineup | unit | `pytest tests/test_constraints.py::test_card_exclude_removes_card -x` | ❌ Wave 0 |
| EXCL-02 | Excluded golfer: all their cards absent from all lineups | unit | `pytest tests/test_constraints.py::test_golfer_exclude_removes_all_cards -x` | ❌ Wave 0 |
| UI-04 | File upload POST clears lock/exclude from session | integration | `pytest tests/test_web.py::test_session_cleared_on_upload -x` | ❌ Wave 0 |
| UI-04 | Banner shown after session reset | integration | `pytest tests/test_web.py::test_reset_banner_shown -x` | ❌ Wave 0 |
| — | Composite key migration: no `id()` reuse in optimize() | unit | `pytest tests/test_optimizer.py -x -q` (update existing) | ✅ needs update |

### Sampling Rate
- **Per task commit:** `pytest tests/test_constraints.py -x -q`
- **Per wave merge:** `pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_constraints.py` — all new constraint unit tests (LOCK-01 through EXCL-02)
- [ ] `gbgolf/optimizer/constraints.py` — ConstraintSet, PreSolveError, check_conflicts, check_feasibility
- [ ] `tests/test_web.py` — add `test_session_cleared_on_upload` and `test_reset_banner_shown`
- [ ] Update `tests/test_optimizer.py` — `test_no_card_reuse_across_contests` and `test_card_uniqueness_all_lineups` to verify composite key behavior

---

## Sources

### Primary (HIGH confidence)
- `gbgolf/optimizer/engine.py` — verified PuLP constraint syntax, function signature, infeasibility return
- `gbgolf/optimizer/__init__.py` — verified `optimize()` loop, `id(c)` usage, `OptimizationResult` structure
- `gbgolf/data/models.py` — verified Card fields (player, salary, multiplier, collection) as composite key components
- `gbgolf/web/routes.py` — verified Flask session absence (not yet used), file upload POST handler structure
- `gbgolf/web/__init__.py` — verified Flask app factory, session not yet configured
- `pyproject.toml` — verified pytest config, installed packages (PuLP >=3.3.0, Flask >=3.0)
- `.planning/phases/04-constraint-foundation/04-CONTEXT.md` — all locked decisions

### Secondary (MEDIUM confidence)
- PuLP documentation pattern for equality constraints (`prob += x[i] == 1`) — standard ILP textbook pattern, consistent with existing code syntax in engine.py

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; all verified against pyproject.toml and existing code
- Architecture: HIGH — all patterns derived directly from existing codebase conventions; ILP constraint syntax verified against engine.py
- Pitfalls: HIGH — derived from concrete analysis of existing `id()` usage, Flask session JSON serialization behavior (float/tuple), and golfer-lock multi-lineup semantics from CONTEXT.md

**Research date:** 2026-03-14
**Valid until:** 2026-04-13 (stable domain; no fast-moving libraries involved)
