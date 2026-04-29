# Fix: Optimizer treats duplicate cards as a single card

## Context

The diagnostic script (`scripts/diagnose_lineup4.py`, run on VPS 2026-04-29) revealed that the user's CSV contains **duplicate rows** for at least 3 cards:

```
Si Woo Kim   $11040 x1.2 '2026 Core'   →  2 CSV rows
Min Woo Lee  $11180 x1.3 '2026 Core'   →  2 CSV rows
Sam Stevens  $10950 x1.5 '2026 Core'   →  2 CSV rows
```

These are real duplicates (the user owns two copies of each card). The platform allows deploying each copy in a separate lineup. The optimizer does not.

The root cause is in [`_card_key`](gbgolf/optimizer/__init__.py:32):

```python
def _card_key(c) -> tuple:
    return (c.player, c.salary, c.multiplier, c.collection)
```

Both copies of a duplicate card produce the same key. After one copy is consumed, the filter at [__init__.py:177](gbgolf/optimizer/__init__.py:177) (`if _card_key(c) not in used_card_keys`) **removes both copies** from the pool for every subsequent lineup.

Observed downstream effect: by Int Tee lineup 4, the pool shrinks to 5 cards (2 Core + 3 Weekly Collection). With `max_entries=4`, `roster_size=5`, all 5 must be selected, but the Weekly Collection limit is 2. PuLP returns `Infeasible` — correctly, given the pool it sees.

The user has expressed reasonable skepticism that duplicates are the *only* cause of the infeasibility. The verification protocol below explicitly re-runs the diagnostic after the fix to confirm — if infeasibility persists, we have a second bug to investigate.

## What also breaks because of the same root cause (besides infeasibility)

Even when the optimizer doesn't go infeasible, the duplicate bug silently caps the user's lineup pool. With 65 valid cards in the CSV but ~3 duplicate pairs, the optimizer effectively has 62 unique slots to fill 56 roster positions across both contests (6×6 + 4×5). Every duplicate the user owns is one slot the optimizer can't see.

Lock semantics also break. [engine.py:71-76](gbgolf/optimizer/engine.py:71) sets `x[i] == 1` for every card matching a locked composite key. With duplicates, locking "Sam Stevens 1.5x" forces **both** copies into the lineup, which then violates the same-player-once-per-lineup constraint and renders the lock infeasible. (Likely currently masked by no user ever locking a duplicated card — but it is broken in the same way.)

## Fix: instance-based identity

Add a per-row instance ID to `Card`. The optimizer tracks **consumed instances**, not composite keys. The composite key stays as a grouping concept for locks, excludes, and future exposure features.

### Files to modify

| File | Change |
|------|--------|
| `gbgolf/data/models.py` | Add `instance_id: int` field to `Card` |
| `gbgolf/data/roster.py` | `_row_to_card` accepts a row index; `parse_roster_csv` enumerates rows and passes index as `instance_id` |
| `gbgolf/data/matching.py` | `match_projections` preserves `instance_id` when constructing enriched cards (verify, may already happen via `replace`/copy) |
| `gbgolf/optimizer/__init__.py` | Replace `used_card_keys: set[tuple]` with `used_instance_ids: set[int]`; filter by `c.instance_id not in used_instance_ids` instead of by composite key; lock/exclude lookup still uses composite key |
| `gbgolf/optimizer/engine.py` | Change card lock from `x[i] == 1` (per match) to `sum(x[i] for matches) >= 1` — fixes the "lock forces both copies" bug discussed above |
| `gbgolf/web/routes.py` | `_serialize_cards` / `_deserialize_cards` carry `instance_id` through the JSON round-trip |
| `tests/test_optimizer.py` | New test: duplicate cards in roster, verify both copies can be used in different lineups; update `test_no_card_reuse_across_contests` to compare by `instance_id`, not composite key |
| `tests/test_roster.py` | Verify `instance_id` is assigned monotonically from row order |
| `scripts/diagnose_lineup4.py` | Fix the verdict-text bug (currently mislabels composite-key collisions as cross-contest depletion); minor, but worth doing while we're here |

### Detailed design

**`Card` dataclass:**
```python
@dataclass
class Card:
    player: str
    salary: int
    multiplier: float
    collection: str
    expires: Optional[date]
    projected_score: Optional[float] = None
    effective_value: Optional[float] = None
    franchise: str = ""
    rookie: str = ""
    instance_id: int = -1  # set by parse_roster_csv from CSV row index; -1 = not yet assigned
```

`-1` default keeps existing test fixtures (which use `make_card` directly) working without forcing them all to pass an ID. Tests that exercise duplicates supply explicit IDs.

**`parse_roster_csv`:**
```python
return [_row_to_card(row, idx) for idx, row in enumerate(reader)]
```
Where `_row_to_card(row, instance_id)` sets `instance_id` on the returned `Card`.

**Optimizer (`__init__.py`):**

```python
used_instance_ids: set[int] = set()

# filter: skip cards whose instance is consumed; composite key still used for excludes
available = [
    c for c in valid_cards
    if c.instance_id not in used_instance_ids
    and _card_key(c) not in excluded_card_keys
    and c.player not in excluded_player_names
]

# after a successful solve:
for card in result:
    used_instance_ids.add(card.instance_id)
```

The `_card_key` function stays — it's still useful for locks, excludes, and any future exposure caps that operate on logical cards rather than instances.

**Phase 2 lock replacement** (`_find_best_replacement` in `__init__.py:37`): the temporary "give cards back" loop currently does `used_card_keys.discard(_card_key(card))` — change to `used_instance_ids.discard(card.instance_id)`. Restoration symmetric.

**Card lock semantics** (`engine.py:71-76`):
```python
if locked_card_keys:
    for locked_key in locked_card_keys:
        matching = [i for i, c in enumerate(cards)
                    if (c.player, c.salary, c.multiplier, c.collection) == locked_key]
        if matching:
            prob += pulp.lpSum(x[i] for i in matching) >= 1
```
This makes card locks behave like golfer locks: at least one of the matching instances is selected. Combined with the same-player-once-per-lineup constraint at [engine.py:67-69](gbgolf/optimizer/engine.py:67), exactly one instance ends up in the lineup.

**Web round-trip**: `_serialize_cards` adds `"instance_id": c.instance_id`, `_deserialize_cards` reads it back. If absent (legacy session data), default to `-1` and reassign deterministically — but realistically, sessions only span a single browser tab, so legacy data isn't a concern.

### Test additions

```python
def test_duplicate_cards_used_in_separate_lineups():
    """User owns 2 copies of a card. Optimizer should use both, in different lineups."""
    cards = [
        # ... 11 unique core cards ...
        make_card("Star Player", 12000, 1.5, "Core", 80.0, instance_id=12),
        make_card("Star Player", 12000, 1.5, "Core", 80.0, instance_id=13),  # duplicate
        # ... rest of pool ...
    ]
    config = [ContestConfig("Test", 30000, 64000, 6, 2, {"Core": 6})]
    result = optimize(cards, config)
    assert len(result.lineups["Test"]) == 2
    used_instance_ids = [c.instance_id for lu in result.lineups["Test"] for c in lu.cards]
    assert 12 in used_instance_ids
    assert 13 in used_instance_ids  # both copies used
```

Update existing `test_no_card_reuse_across_contests` to assert disjointness on `instance_id`, not composite key.

## Verification

After implementing the fix, do all of the following on the VPS (script is still at `/tmp/diagnose_lineup4.py`, CSV still at `/tmp/diagnose_roster.csv`):

1. **Run unit tests** (locally): `pytest tests/` — all existing tests must pass; new duplicate-card test must pass.

2. **Deploy to VPS** via the existing `bash deploy/deploy.sh` workflow (one approval; user explicitly authorizes the deploy).

3. **Re-upload the diagnostic script to VPS** (since it was updated to fix the verdict-text bug):
   ```
   scp scripts/diagnose_lineup4.py deploy@193.46.198.60:/tmp/diagnose_lineup4.py
   ```

4. **Re-run the diagnostic against the same CSV**:
   ```
   ssh deploy@193.46.198.60 "cd /opt/GBGolfOptimizer && .venv/bin/python /tmp/diagnose_lineup4.py --csv /tmp/diagnose_roster.csv"
   ```

5. **Expected result after fix:**
   - Step 2 still reports composite-key collisions (you do own duplicates — that's a fact about the CSV, not a bug).
   - Step 3 shows `The Intermediate Tee: 4 lineup(s) built` — no infeasibility notice.
   - Step 4 shows lineup 4 attempted with a **larger pool** than the buggy 5-card pool, and `RESULT: OK`.
   - Verdict: no failure to classify.

6. **If infeasibility persists** (the user's hedge): the duplicates were not the (sole) cause. We then have a second, independent bug — and the diagnostic output will show what state the pool is in at lineup 4 under the fixed instance-tracking, which is much better evidence than we had this round. Write a new plan against that evidence.

7. **Cleanup once verified:**
   ```
   ssh deploy@193.46.198.60 "rm /tmp/diagnose_roster.csv /tmp/diagnose_lineup4.py"
   ```

## Out of scope

- Per-contest `used_instance_ids` (cross-contest sharing is intentional per the platform rule documented in memory; the bug is about same-key duplicates, not cross-contest reuse).
- Exposure caps / diversity constraints (separate ADV-01 / ADV-02 backlog items).
- Global ILP rewrite (was a premature fix proposal in the prior plan; not needed once instance tracking is correct).
- UI changes to surface duplicate-card detection (could be added later as a hint in the player pool, but not required to fix the bug).
