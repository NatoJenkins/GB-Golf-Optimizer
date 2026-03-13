# Phase 2: Optimization Engine - Research

**Researched:** 2026-03-13
**Domain:** Integer Linear Programming (ILP) for multi-lineup DFS-style contest optimization
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Each physical card is a distinct, consumable asset: once assigned to any lineup, it cannot appear in any other lineup across any contest
- The same golfer MAY appear in multiple lineup entries, as long as each appearance uses a different card
- Within a single lineup entry, a golfer may only appear ONCE (regardless of how many cards owned)
- Constraint is card-level (not golfer-level) for cross-lineup locking
- Sequential solve: build lineups one at a time — Tips lineup 1, Tips lineup 2, Tips lineup 3, then Intermediate Tee lineup 1, Intermediate Tee lineup 2
- After each lineup is solved, those cards are removed from the available pool before solving the next
- Same sequential approach applies to both contests
- Intermediate Tee solves from whatever cards remain after all 3 Tips lineups are assigned
- If a lineup cannot be built (infeasible), do NOT stop entirely — return however many lineups were successfully built
- Include an infeasibility notice for each lineup that could not be constructed
- General message only: "Could not build lineup N for [Contest Name]" — no diagnostic analysis
- Returns a dict grouped by contest name: `{'The Tips': [...], 'The Intermediate Tee': [...]}`
- Full OptimizationResult includes: `lineups` (dict), `unused_cards` (list of Card), `infeasibility_notices` (list of str)

### Claude's Discretion
- ILP solver library choice (PuLP or OR-Tools — both mentioned in project constraints)
- Exact Lineup dataclass fields beyond the required set
- How ties in objective value are broken within a single solve

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| OPT-01 | Optimizer generates 3 optimal lineups for The Tips contest (6 golfers per lineup, salary $30,000–$64,000, max 3 Weekly Collection cards, max 6 Core cards) | ILP binary variable formulation with salary range and collection limit constraints |
| OPT-02 | Optimizer generates 2 optimal lineups for The Intermediate Tee contest (5 golfers per lineup, salary $20,000–$52,000, max 2 Weekly Collection cards, max 5 Core cards) | Same ILP formulation applied to remaining card pool after Tips solve |
| OPT-03 | Cash contest (The Tips) is fully optimized first; Intermediate Tee lineups use only cards not already assigned to Tips lineups | Sequential solve with card pool mutation after each lineup |
| OPT-04 | Each card may appear in at most one lineup across all contests (cards are locked per lineup) | Card-level binary variables; pool filtering between solves enforces uniqueness |
| OPT-06 | Optimizer respects both the salary floor (minimum) and salary cap (maximum) for each contest | Two salary constraints per solve: lpSum(salary) >= salary_min and <= salary_max |
</phase_requirements>

---

## Summary

The optimization problem is a variant of the 0/1 knapsack problem: select exactly N binary-valued cards from a pool to maximize total effective_value subject to salary range and collection count constraints. Each ILP solve selects one lineup; the sequential strategy removes used cards from the pool and re-solves up to max_entries times per contest.

PuLP 3.3.0 is the correct choice for this project. It ships with the COIN-OR CBC solver bundled — no system-level install required, just `pip install pulp`. OR-Tools is a heavier dependency (binary wheel ~100MB) and its Python MIP API has changed across versions; PuLP's API is stable and the problem size (5–6 binary variables chosen from likely 20–60 cards) is trivially small for CBC.

The key ILP formulation insight: each card gets one binary variable (0=not selected, 1=selected). The same golfer may appear at most once per lineup — this requires a per-player summing constraint. Across lineups, uniqueness is enforced by removing selected cards from the pool entirely before the next solve, not by adding cross-solve constraints to a single ILP instance.

**Primary recommendation:** Use PuLP 3.3.0 with CBC solver. Sequential single-lineup ILP solves. Card pool is a mutable Python list; remove selected cards after each successful solve. Wrap each solve in a try/except + status check; on non-optimal status, append to infeasibility_notices and continue.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PuLP | 3.3.0 | ILP modelling + solving | CBC solver bundled; no extra installs; stable API; widely used for DFS-style problems |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python dataclasses | stdlib | Lineup, OptimizationResult types | Matches established project pattern |
| typing | stdlib | Type hints for result structures | Matches established project pattern |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PuLP | OR-Tools (ortools) | OR-Tools is more powerful but ~100MB wheel, API changed in v9.x, overkill for 5–6 card selection from <100 options |
| PuLP | scipy.optimize.milp | scipy.milp available in scipy>=1.7 but scipy is a large dependency; PuLP's constraint DSL is cleaner for this use case |
| Sequential solve | Single multi-lineup ILP | Single ILP with "at most one card per slot across lineups" is more complex to formulate and harder to debug; sequential is explicitly preferred |

**Installation:**
```bash
pip install pulp>=3.3.0
```

Then add to `pyproject.toml` dependencies:
```toml
dependencies = [
    "pydantic>=2.0",
    "python-dateutil>=2.9",
    "pulp>=3.3.0",
]
```

---

## Architecture Patterns

### Recommended Module Structure
```
gbgolf/
├── optimizer/
│   ├── __init__.py       # Public API: optimize(), OptimizationResult, Lineup
│   └── engine.py         # ILP formulation and solve logic (_solve_one_lineup, _build_problem)
tests/
└── test_optimizer.py     # Unit tests for optimizer module
```

The `gbgolf/optimizer/` module is a sibling to `gbgolf/data/`. Phase 3 imports `from gbgolf.optimizer import optimize, OptimizationResult`.

### Pattern 1: Binary Card Selection ILP

**What:** Each card in the current pool gets a binary decision variable. Objective maximizes sum of effective_value for selected cards. Constraints: roster_size exact selection, salary floor, salary cap, collection limits, same-golfer-once-per-lineup.

**When to use:** Every single-lineup solve call.

**Example:**
```python
# Source: PuLP 3.3.0 docs + verified DFS pattern
import pulp

def _solve_one_lineup(cards: list[Card], config: ContestConfig) -> list[Card] | None:
    """Returns selected cards or None if infeasible."""
    prob = pulp.LpProblem("lineup", pulp.LpMaximize)

    # One binary variable per card (index is position in list)
    x = pulp.LpVariable.dicts("card", range(len(cards)), cat="Binary")

    # Objective: maximize total effective value
    prob += pulp.lpSum(cards[i].effective_value * x[i] for i in range(len(cards)))

    # Exactly roster_size cards
    prob += pulp.lpSum(x[i] for i in range(len(cards))) == config.roster_size

    # Salary floor and cap
    prob += pulp.lpSum(cards[i].salary * x[i] for i in range(len(cards))) >= config.salary_min
    prob += pulp.lpSum(cards[i].salary * x[i] for i in range(len(cards))) <= config.salary_max

    # Collection limits (e.g., max 3 Weekly Collection, max 6 Core)
    for collection_name, limit in config.collection_limits.items():
        eligible = [i for i, c in enumerate(cards) if c.collection == collection_name]
        prob += pulp.lpSum(x[i] for i in eligible) <= limit

    # Same golfer at most once per lineup
    players = {c.player for c in cards}
    for player in players:
        player_cards = [i for i, c in enumerate(cards) if c.player == player]
        if len(player_cards) > 1:
            prob += pulp.lpSum(x[i] for i in player_cards) <= 1

    # Solve (msg=0 suppresses CBC output)
    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    if pulp.LpStatus[prob.status] != "Optimal":
        return None  # Infeasible or other failure

    return [cards[i] for i in range(len(cards)) if x[i].varValue > 0.5]
```

### Pattern 2: Sequential Solve with Pool Mutation

**What:** Iterate up to max_entries times per contest. After each successful solve, remove selected cards from the pool list. On infeasibility, record a notice and continue.

**When to use:** Top-level `optimize()` function.

**Example:**
```python
def optimize(valid_cards: list[Card], contests: list[ContestConfig]) -> OptimizationResult:
    pool = list(valid_cards)  # mutable copy
    lineups: dict[str, list] = {}
    notices: list[str] = []

    for contest in contests:  # Tips first, then Intermediate Tee
        contest_lineups = []
        for n in range(1, contest.max_entries + 1):
            selected = _solve_one_lineup(pool, contest)
            if selected is None:
                notices.append(f"Could not build lineup {n} for {contest.name}")
            else:
                contest_lineups.append(Lineup(cards=selected, contest=contest.name))
                # Remove used cards from pool (card-level uniqueness)
                used_ids = {id(c) for c in selected}
                pool = [c for c in pool if id(c) not in used_ids]
        lineups[contest.name] = contest_lineups

    return OptimizationResult(
        lineups=lineups,
        unused_cards=pool,
        infeasibility_notices=notices,
    )
```

### Pattern 3: Result Data Structures

**What:** Dataclasses following the established project pattern (not Pydantic — those are boundary-only).

```python
from dataclasses import dataclass, field

@dataclass
class Lineup:
    contest: str
    cards: list  # list[Card]
    # Computed properties useful for Phase 3 display:
    total_salary: int = field(init=False)
    total_projected_score: float = field(init=False)
    total_effective_value: float = field(init=False)

    def __post_init__(self):
        self.total_salary = sum(c.salary for c in self.cards)
        self.total_projected_score = sum(c.projected_score for c in self.cards)
        self.total_effective_value = sum(c.effective_value for c in self.cards)


@dataclass
class OptimizationResult:
    lineups: dict  # dict[str, list[Lineup]]
    unused_cards: list  # list[Card]
    infeasibility_notices: list  # list[str]
```

### Anti-Patterns to Avoid

- **Global pool mutation across ILP instances:** Each solve must work on the current filtered pool snapshot; never add "not already used" as an ILP constraint across separate solve calls — just remove from the list.
- **Using `varValue == 1`:** Float comparison after ILP solve. Use `varValue > 0.5` to account for floating-point rounding in CBC's output.
- **Raising on infeasibility:** The decision is to continue and collect notices, not raise ValueError. Infeasibility is not an error condition here.
- **Using `id()` for card identity naively:** Python's `id()` is safe within one run (pool list is never rebuilt). However, using object identity is more robust than index-based tracking across pool mutations.
- **Single large ILP for all 5 lineups:** This was explicitly rejected. Sequential is the locked decision.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ILP solve | Custom brute-force or greedy selector | PuLP + CBC | ILP handles combinatorial explosion; greedy can miss optimal solutions with salary floor constraints |
| Salary feasibility check | Pre-solve heuristic to "estimate" if salary range is achievable | Let CBC determine infeasibility | Salary floor + cap + collection limits interact in non-obvious ways; CBC's branch-and-bound is correct |
| Tie-breaking between equal-value lineups | Custom comparator | Accept CBC's arbitrary choice | Problem is small enough that multiple optima don't matter for correctness |

**Key insight:** With only 5–6 slots and likely 20–60 valid cards, CBC solves each lineup in milliseconds. The engineering effort of a correct ILP formulation is much lower than a correct greedy algorithm that handles salary floors, collection limits, and same-player constraints simultaneously.

---

## Common Pitfalls

### Pitfall 1: Salary Floor Makes Problems Infeasible Unexpectedly
**What goes wrong:** A small card pool (after several Tips lineups consume cards) may not be able to meet the salary floor with the available cards.
**Why it happens:** With few cards remaining, the cheapest N-card combination still falls below salary_min.
**How to avoid:** This is expected behavior — return None from `_solve_one_lineup`, add infeasibility notice, continue. Do not pre-filter or raise.
**Warning signs:** Multiple consecutive infeasibility notices for later lineup numbers.

### Pitfall 2: Collection Limits Can Overconstrain
**What goes wrong:** `collection_limits` specifies maximum counts (e.g., max 3 Weekly Collection). If the pool has only 2 Weekly Collection cards and 10 Core cards, selecting 6 from Core is fine. But if `collection_limits` is misread as a minimum requirement, no Core-only lineup would be "permitted."
**Why it happens:** Misreading the contest spec — limits are caps, not floors.
**How to avoid:** All collection constraints are `<=` (upper bound), never `==` or `>=`. Verify against `VALID_CONFIG_DICT` in conftest.py: `{"Weekly Collection": 3, "Core": 6}` means at most 3 and at most 6 — a lineup with 0 Weekly Collection cards is legal.

### Pitfall 3: Same-Golfer-Per-Lineup Constraint Omission
**What goes wrong:** A player with two Core cards at different salaries may be selected twice if the constraint is missing, violating the within-lineup uniqueness rule from CONTEXT.md.
**Why it happens:** CBC optimizes without any inherent "only pick one per player" logic — it only knows cards, not players.
**How to avoid:** Include the per-player `lpSum(x[i] for i in player_cards) <= 1` constraint for all players who appear more than once in the current pool.

### Pitfall 4: Card Identity Confusion After Pool Filtering
**What goes wrong:** Using index-based references (e.g., "remove index 3") breaks when pool is rebuilt as a new list.
**Why it happens:** Pool filtering creates new lists; old indices are stale.
**How to avoid:** Use `id(card)` for identity tracking within a single `optimize()` call, or filter by object reference equality. The `Card` dataclass uses default equality (field-based), which could incorrectly equate two different cards for the same player with the same stats — use `id()` or ensure cards are matched by object reference.

### Pitfall 5: CBC Output Noise in Tests
**What goes wrong:** CBC prints solver progress to stdout during tests, making test output noisy.
**Why it happens:** Default `msg=1` in PuLP shows solver log.
**How to avoid:** Always pass `pulp.PULP_CBC_CMD(msg=0)` in production and test code.

### Pitfall 6: Unresolved Blocker from STATE.md — Franchise/Rookie as Collection Types
**What goes wrong:** The STATE.md records an unresolved question: "Franchise/Rookie CSV columns: unclear whether these are separate collection types requiring ILP constraints or boolean flags."
**Why it happens:** The Card dataclass stores `franchise: str` and `rookie: str` but their semantics for collection limiting are undefined.
**How to avoid:** The `collection_limits` dict in ContestConfig is keyed by collection name (e.g., "Weekly Collection", "Core"). The current contest config does NOT contain "Franchise" or "Rookie" keys. Therefore, for Phase 2, treat `collection` field only (not `franchise`/`rookie`) when applying collection constraints. The constraint loop over `config.collection_limits.items()` naturally handles only what the config specifies — no change required.

---

## Code Examples

### Full Single-Lineup Solve
```python
# Source: PuLP 3.3.0 API + verified DFS pattern
import pulp
from gbgolf.data.models import Card
from gbgolf.data.config import ContestConfig

def _solve_one_lineup(cards: list[Card], config: ContestConfig) -> list[Card] | None:
    prob = pulp.LpProblem("lineup", pulp.LpMaximize)
    n = len(cards)
    x = pulp.LpVariable.dicts("card", range(n), cat="Binary")

    # Objective
    prob += pulp.lpSum(cards[i].effective_value * x[i] for i in range(n))

    # Exactly roster_size selected
    prob += pulp.lpSum(x[i] for i in range(n)) == config.roster_size

    # Salary range
    prob += pulp.lpSum(cards[i].salary * x[i] for i in range(n)) >= config.salary_min
    prob += pulp.lpSum(cards[i].salary * x[i] for i in range(n)) <= config.salary_max

    # Collection limits (upper bounds)
    for coll_name, limit in config.collection_limits.items():
        eligible = [i for i, c in enumerate(cards) if c.collection == coll_name]
        if eligible:
            prob += pulp.lpSum(x[i] for i in eligible) <= limit

    # Same player at most once per lineup
    for player in {c.player for c in cards}:
        idxs = [i for i, c in enumerate(cards) if c.player == player]
        if len(idxs) > 1:
            prob += pulp.lpSum(x[i] for i in idxs) <= 1

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    if pulp.LpStatus[prob.status] != "Optimal":
        return None

    return [cards[i] for i in range(n) if x[i].varValue > 0.5]
```

### Status Check Pattern
```python
# Source: PuLP 3.3.0 docs
prob.solve(pulp.PULP_CBC_CMD(msg=0))
status_str = pulp.LpStatus[prob.status]
# status_str is one of: "Optimal", "Infeasible", "Unbounded", "Undefined", "Not Solved"
if status_str == "Optimal":
    selected = [cards[i] for i in range(n) if x[i].varValue > 0.5]
```

### Variable Value Extraction
```python
# Use > 0.5 not == 1 to handle floating-point output from CBC
selected_cards = [cards[i] for i in range(len(cards)) if x[i].varValue > 0.5]
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PuLP 2.x with GLPK dependency | PuLP 3.x with CBC bundled | ~2020 | No solver install required; `pip install pulp` is self-contained |
| OR-Tools CP-SAT API (v8) | OR-Tools 9.x (different API) | 2022–2023 | API migration cost; not relevant since we're using PuLP |

**Deprecated/outdated:**
- `LpVariable` with `cat='Integer'` + `lowBound=0, upBound=1`: Still works but `cat='Binary'` is more explicit and idiomatic.
- `prob.solve()` without specifying solver: Works (uses default CBC), but `pulp.PULP_CBC_CMD(msg=0)` is recommended to suppress output.

---

## Open Questions

1. **Card dataclass equality for pool filtering**
   - What we know: `Card` is a plain dataclass; default `__eq__` compares all fields. Two cards for the same player with identical stats would be considered equal by `==`.
   - What's unclear: Are there ever two cards in the real data that would be field-identical but are physically different cards? (e.g., same player, same salary, same multiplier, same collection — duplicates)
   - Recommendation: Use `id(card)` for pool filtering to be safe. If Phase 3 needs JSON serialization of cards, add a unique card_id field in a future phase.

2. **JSON serializability of OptimizationResult**
   - What we know: CONTEXT.md states "Result must be serializable to JSON (for Phase 3 HTTP response)." Dataclasses with `date` fields are not JSON serializable by default.
   - What's unclear: Phase 3 hasn't been designed yet; the serialization boundary is unclear.
   - Recommendation: Keep OptimizationResult as a plain dataclass for Phase 2. Add a `to_dict()` method or note for Phase 3 to handle serialization at the API boundary (consistent with the Pydantic-at-boundary pattern from Phase 1).

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `python -m pytest tests/test_optimizer.py -x -q` |
| Full suite command | `python -m pytest -x -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| OPT-01 | Optimizer returns 3 Tips lineups, each with 6 cards | unit | `python -m pytest tests/test_optimizer.py::test_tips_lineup_count -x` | Wave 0 |
| OPT-01 | Tips lineups respect salary floor and cap | unit | `python -m pytest tests/test_optimizer.py::test_tips_salary_constraints -x` | Wave 0 |
| OPT-01 | Tips lineups respect collection limits | unit | `python -m pytest tests/test_optimizer.py::test_tips_collection_limits -x` | Wave 0 |
| OPT-02 | Optimizer returns 2 Intermediate Tee lineups with 5 cards each | unit | `python -m pytest tests/test_optimizer.py::test_intermediate_lineup_count -x` | Wave 0 |
| OPT-03 | Intermediate Tee cards are disjoint from Tips cards | unit | `python -m pytest tests/test_optimizer.py::test_no_card_reuse_across_contests -x` | Wave 0 |
| OPT-04 | No card appears in more than one lineup | unit | `python -m pytest tests/test_optimizer.py::test_card_uniqueness_all_lineups -x` | Wave 0 |
| OPT-06 | Salary floor and cap enforced per lineup | unit | `python -m pytest tests/test_optimizer.py::test_salary_floor_enforced -x` | Wave 0 |
| OPT-01/OPT-02 | Infeasible pool returns notices, not crash | unit | `python -m pytest tests/test_optimizer.py::test_infeasibility_notice -x` | Wave 0 |
| OPT-01/OPT-02 | Partial results returned when only some lineups can be built | unit | `python -m pytest tests/test_optimizer.py::test_partial_results -x` | Wave 0 |
| OPT-04 | Same player does not appear twice in one lineup | unit | `python -m pytest tests/test_optimizer.py::test_same_player_once_per_lineup -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_optimizer.py -x -q`
- **Per wave merge:** `python -m pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_optimizer.py` — all optimizer tests (file does not exist yet)
- [ ] PuLP install: `pip install pulp>=3.3.0` and add to `pyproject.toml` dependencies
- [ ] `gbgolf/optimizer/__init__.py` — public API module (does not exist yet)
- [ ] `gbgolf/optimizer/engine.py` — ILP engine (does not exist yet)

---

## Sources

### Primary (HIGH confidence)
- PyPI PuLP 3.3.0 (pypi.org/project/PuLP/) — current version, release date (Sep 2025), CBC bundled confirmed
- PuLP official docs (coin-or.github.io/pulp/) — LpProblem, LpVariable, lpSum, prob.status API
- Existing codebase (gbgolf/data/models.py, config.py, __init__.py) — Card, ContestConfig, ValidationResult structures

### Secondary (MEDIUM confidence)
- PuLP DraftKings DFS pattern (zwlevonian.medium.com — 403'd but WebSearch confirmed pattern) — binary variable per player, salary cap constraint, category/position constraint
- PuLP Part 4 tutorial (benalexkeen.com) — LpVariable.dicts, lpSum, constraint syntax, solve + status check

### Tertiary (LOW confidence)
- WebSearch: "DFS lineup optimizer PuLP Python" — confirmed PuLP is the standard library for this problem class; specific DFS code not directly verified from official source

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — PuLP 3.3.0 with CBC bundled confirmed from PyPI official page; no solver install required
- Architecture: HIGH — ILP formulation follows established patterns; sequential solve is locked decision from CONTEXT.md; data structures follow existing project conventions
- Pitfalls: HIGH for salary/collection constraints (verified from ILP theory + PuLP docs); MEDIUM for card identity pitfall (reasoning from code inspection)

**Research date:** 2026-03-13
**Valid until:** 2026-09-13 (PuLP is stable; CBC solver bundling is a long-standing design decision)
