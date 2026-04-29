"""Tests for the optimizer module.

Covers:
- Tips lineup count and constraints
- Intermediate Tee lineup count
- Card reuse and uniqueness (composite key deduplication)
- Infeasibility handling
- Lock/exclude behavioral tests (ConstraintSet integration)
"""
from datetime import date

import pytest

from gbgolf.data.models import Card
from gbgolf.data.config import ContestConfig
from gbgolf.optimizer import optimize, OptimizationResult, Lineup
from gbgolf.optimizer.constraints import ConstraintSet


# ---------------------------------------------------------------------------
# Card builder helper
# ---------------------------------------------------------------------------

_next_instance_id = 0


def make_card(player, salary, multiplier, collection, projected_score, effective_value=None,
              instance_id=None):
    """Test card builder. Auto-assigns a monotonic instance_id unless overridden.

    Pass instance_id explicitly when a test needs to fabricate composite-key
    duplicates that share player+salary+multiplier+collection but have distinct
    IDs (the on-platform "I own two of this card" case).
    """
    global _next_instance_id
    if instance_id is None:
        instance_id = _next_instance_id
        _next_instance_id += 1
    ev = effective_value if effective_value is not None else round(projected_score * multiplier, 4)
    return Card(
        player=player,
        salary=salary,
        multiplier=multiplier,
        collection=collection,
        expires=date(2026, 12, 31),
        instance_id=instance_id,
        projected_score=projected_score,
        effective_value=ev,
    )


# ---------------------------------------------------------------------------
# Module-level fixtures: Tips contest (6-man roster, max 3 entries)
# ---------------------------------------------------------------------------

TIPS_CONFIG = [
    ContestConfig(
        name="The Tips",
        salary_min=30000,
        salary_max=64000,
        roster_size=6,
        max_entries=3,
        collection_limits={"Weekly Collection": 3, "Core": 6},
    )
]

TIPS_CARDS = [
    make_card("Scottie Scheffler",   12000, 1.5, "Core",              72.5),
    make_card("Rory McIlroy",        11000, 1.2, "Weekly Collection", 68.3),
    make_card("Collin Morikawa",     10000, 1.4, "Weekly Collection", 70.2),
    make_card("Xander Schauffele",    9500, 1.2, "Core",              67.8),
    make_card("Ludvig Aberg",         9000, 1.3, "Core",              65.1),
    make_card("Viktor Hovland",       9000, 1.1, "Core",              63.4),
    make_card("Jon Rahm",             8500, 1.2, "Weekly Collection", 66.0),
    make_card("Tommy Fleetwood",      8000, 1.1, "Core",              60.0),
    make_card("Shane Lowry",          8000, 1.0, "Core",              58.5),
    make_card("Tony Finau",           8000, 1.0, "Core",              57.0),
    make_card("Matt Fitzpatrick",     8500, 1.1, "Core",              61.2),
    make_card("Wyndham Clark",        8000, 1.0, "Weekly Collection", 55.0),
    # 6 extra cards so 3 disjoint 6-card lineups are feasible (3 x 6 = 18 cards minimum)
    make_card("Patrick Cantlay",      8500, 1.1, "Core",              59.0),
    make_card("Tyrrell Hatton",       8000, 1.0, "Core",              56.0),
    make_card("Sam Burns",            8000, 1.0, "Core",              54.0),
    make_card("Russell Henley",       8000, 1.0, "Core",              53.0),
    make_card("Keegan Bradley",       8000, 1.0, "Core",              52.0),
    make_card("Hideki Matsuyama",     9000, 1.1, "Core",              62.0),
]

# ---------------------------------------------------------------------------
# Module-level fixtures: all contests + large card pool for multi-contest tests
# ---------------------------------------------------------------------------

ALL_CONTESTS = [
    ContestConfig(
        name="The Tips",
        salary_min=30000,
        salary_max=64000,
        roster_size=6,
        max_entries=3,
        collection_limits={"Weekly Collection": 3, "Core": 6},
    ),
    ContestConfig(
        name="The Intermediate Tee",
        salary_min=20000,
        salary_max=52000,
        roster_size=5,
        max_entries=2,
        collection_limits={"Weekly Collection": 2, "Core": 5},
    ),
]

# 35 unique cards for multi-contest tests: enough for 3 Tips lineups (3x6=18) plus
# 2 Intermediate Tee lineups (2x5=10) with 7 cards unused (18+10+7=35)
ALL_CARDS = [
    make_card(f"Player {i:02d}", 8000 + (i * 200), 1.0 + (i * 0.05), "Core", 55.0 + i)
    for i in range(30)
] + [
    make_card(f"Weekly Player {i:02d}", 9000 + (i * 150), 1.1 + (i * 0.05), "Weekly Collection", 58.0 + i)
    for i in range(5)
]


# ---------------------------------------------------------------------------
# Tests: The Tips lineup count and constraints
# ---------------------------------------------------------------------------

def test_tips_lineup_count():
    """optimize() returns result where result.lineups['The Tips'] has length 3."""
    result = optimize(TIPS_CARDS, TIPS_CONFIG)
    assert len(result.lineups["The Tips"]) == 3


def test_tips_salary_constraints():
    """Each Tips lineup total_salary is within [30000, 64000]."""
    result = optimize(TIPS_CARDS, TIPS_CONFIG)
    for lineup in result.lineups["The Tips"]:
        assert lineup.total_salary >= 30000, f"Lineup below salary floor: {lineup.total_salary}"
        assert lineup.total_salary <= 64000, f"Lineup above salary cap: {lineup.total_salary}"


def test_tips_collection_limits():
    """Each Tips lineup has at most 3 Weekly Collection cards and at most 6 Core cards."""
    result = optimize(TIPS_CARDS, TIPS_CONFIG)
    for lineup in result.lineups["The Tips"]:
        weekly_count = sum(1 for c in lineup.cards if c.collection == "Weekly Collection")
        core_count = sum(1 for c in lineup.cards if c.collection == "Core")
        assert weekly_count <= 3, f"Too many Weekly Collection cards: {weekly_count}"
        assert core_count <= 6, f"Too many Core cards: {core_count}"


def test_same_player_once_per_lineup():
    """No player name appears more than once in any single lineup's cards."""
    result = optimize(TIPS_CARDS, TIPS_CONFIG)
    for contest_name, lineups in result.lineups.items():
        for lineup in lineups:
            players = [c.player for c in lineup.cards]
            assert len(players) == len(set(players)), (
                f"Duplicate player in {contest_name} lineup: {players}"
            )


# ---------------------------------------------------------------------------
# Tests: The Intermediate Tee lineup count
# ---------------------------------------------------------------------------

def test_intermediate_lineup_count():
    """result.lineups['The Intermediate Tee'] has length 2."""
    result = optimize(ALL_CARDS, ALL_CONTESTS)
    assert len(result.lineups["The Intermediate Tee"]) == 2


# ---------------------------------------------------------------------------
# Tests: Card reuse and uniqueness across contests
# ---------------------------------------------------------------------------

def test_no_card_reuse_across_contests():
    """Card instances used in Tips lineups are disjoint from those in Intermediate Tee lineups.

    Compares by instance_id (not composite key) because the user may legitimately
    own two copies of the same card (matching composite keys, distinct instance IDs)
    and deploy each copy in a separate lineup, including across contests.
    """
    result = optimize(ALL_CARDS, ALL_CONTESTS)
    tips_ids = {
        card.instance_id
        for lineup in result.lineups.get("The Tips", [])
        for card in lineup.cards
    }
    inter_ids = {
        card.instance_id
        for lineup in result.lineups.get("The Intermediate Tee", [])
        for card in lineup.cards
    }
    overlap = tips_ids & inter_ids
    assert not overlap, f"Card instances reused across contests: {len(overlap)} instance(s)"


def test_card_uniqueness_all_lineups():
    """No card instance appears in more than one lineup across all contests."""
    result = optimize(ALL_CARDS, ALL_CONTESTS)
    seen_ids: set = set()
    for contest_name, lineups in result.lineups.items():
        for lineup in lineups:
            for card in lineup.cards:
                assert card.instance_id not in seen_ids, (
                    f"Card '{card.player}' (instance {card.instance_id}) reused in {contest_name}"
                )
                seen_ids.add(card.instance_id)


# ---------------------------------------------------------------------------
# Tests: Infeasibility handling
# ---------------------------------------------------------------------------

def test_salary_floor_enforced():
    """A card pool where no 6-card combo can meet salary_min returns infeasibility notice, not a crash."""
    cheap_cards = [
        make_card(f"Cheap {i}", 1000, 1.0, "Core", 50.0 + i)
        for i in range(10)
    ]
    # salary_min=30000 but max possible 6-card salary = 6*1000+5*100... well under floor
    config = [ContestConfig("The Tips", 30000, 64000, 6, 3, {"Weekly Collection": 3, "Core": 6})]
    result = optimize(cheap_cards, config)
    assert isinstance(result.infeasibility_notices, list)
    assert len(result.infeasibility_notices) > 0


def test_infeasibility_notice():
    """result.infeasibility_notices is a list of strings when lineup cannot be built."""
    cheap_cards = [
        make_card(f"Cheap {i}", 500, 1.0, "Core", 40.0 + i)
        for i in range(8)
    ]
    config = [ContestConfig("The Tips", 30000, 64000, 6, 1, {"Weekly Collection": 3, "Core": 6})]
    result = optimize(cheap_cards, config)
    assert isinstance(result.infeasibility_notices, list)
    for notice in result.infeasibility_notices:
        assert isinstance(notice, str), f"Expected str notice, got: {type(notice)}"


def test_partial_results():
    """When only 2 of 3 Tips lineups can be built, result.lineups['The Tips'] has 2 items and infeasibility_notices has 1 entry."""
    # 12 cards: enough for 2 lineups of 6 but not 3
    cards = [
        make_card(f"Player {i:02d}", 8000 + (i * 100), 1.0 + (i * 0.1), "Core", 60.0 + i)
        for i in range(12)
    ]
    config = [
        ContestConfig("The Tips", 30000, 64000, 6, 3, {"Weekly Collection": 3, "Core": 6})
    ]
    result = optimize(cards, config)
    assert len(result.lineups["The Tips"]) == 2
    assert len(result.infeasibility_notices) == 1


# ---------------------------------------------------------------------------
# Tests: Lock and exclude behavioral tests (ConstraintSet integration)
# ---------------------------------------------------------------------------

def test_card_lock_forces_card_into_lineup():
    """Locking Scottie Scheffler's card forces him into lineup 1 of The Tips."""
    scheffler_key = ("Scottie Scheffler", 12000, 1.5, "Core")
    cs = ConstraintSet(locked_cards=[scheffler_key])
    result = optimize(TIPS_CARDS, TIPS_CONFIG, constraints=cs)
    assert len(result.lineups["The Tips"]) >= 1, "Expected at least one lineup"
    lineup_1_players = [c.player for c in result.lineups["The Tips"][0].cards]
    assert "Scottie Scheffler" in lineup_1_players, (
        f"Scheffler not in lineup 1: {lineup_1_players}"
    )


def test_golfer_lock_satisfied_in_some_lineup():
    """Locked golfer appears in at least one lineup; all slots fill and no infeasibility."""
    cs = ConstraintSet(locked_golfers=["Jon Rahm"])
    result = optimize(TIPS_CARDS, TIPS_CONFIG, constraints=cs)
    all_players = [c.player for lu in result.lineups["The Tips"] for c in lu.cards]
    assert "Jon Rahm" in all_players, (
        f"Jon Rahm not found in any lineup: {all_players}"
    )
    assert len(result.lineups["The Tips"]) == 3, (
        "Expected 3 lineups; golfer lock should not reduce lineup count"
    )
    assert not result.infeasibility_notices, (
        f"Unexpected infeasibility notices: {result.infeasibility_notices}"
    )


def test_multiple_golfer_locks_all_satisfied():
    """Multiple locked golfers each appear in at least one lineup with no infeasibility."""
    cs = ConstraintSet(locked_golfers=["Scottie Scheffler", "Rory McIlroy"])
    result = optimize(TIPS_CARDS, TIPS_CONFIG, constraints=cs)
    all_players = [c.player for lu in result.lineups["The Tips"] for c in lu.cards]
    assert "Scottie Scheffler" in all_players, "Scheffler not found in any lineup"
    assert "Rory McIlroy" in all_players, "McIlroy not found in any lineup"
    assert len(result.lineups["The Tips"]) == 3
    assert not result.infeasibility_notices, (
        f"Unexpected infeasibility notices: {result.infeasibility_notices}"
    )


def test_exclude_card_absent_from_all_lineups():
    """An excluded card key never appears in any lineup."""
    scheffler_key = ("Scottie Scheffler", 12000, 1.5, "Core")
    cs = ConstraintSet(excluded_cards=[scheffler_key])
    result = optimize(TIPS_CARDS, TIPS_CONFIG, constraints=cs)
    for lineup in result.lineups.get("The Tips", []):
        lineup_keys = [
            (c.player, c.salary, c.multiplier, c.collection)
            for c in lineup.cards
        ]
        assert scheffler_key not in lineup_keys, (
            f"Excluded card {scheffler_key} found in lineup: {lineup_keys}"
        )


def test_exclude_golfer_absent_from_all_lineups():
    """Excluding 'Scottie Scheffler' by name means no Scheffler card appears in any lineup."""
    cs = ConstraintSet(excluded_players=["Scottie Scheffler"])
    result = optimize(TIPS_CARDS, TIPS_CONFIG, constraints=cs)
    for lineup in result.lineups.get("The Tips", []):
        players = [c.player for c in lineup.cards]
        assert "Scottie Scheffler" not in players, (
            f"Excluded player Scottie Scheffler found in lineup: {players}"
        )


def test_conflict_returns_error_not_lineups():
    """Locking and excluding the same player returns infeasibility_notices with no lineups built."""
    scheffler_key = ("Scottie Scheffler", 12000, 1.5, "Core")
    cs = ConstraintSet(
        locked_cards=[scheffler_key],
        excluded_cards=[scheffler_key],
    )
    result = optimize(TIPS_CARDS, TIPS_CONFIG, constraints=cs)
    # All contests should have empty lineup lists
    for contest_lineups in result.lineups.values():
        assert contest_lineups == [], (
            f"Expected no lineups on conflict, got: {contest_lineups}"
        )
    assert len(result.infeasibility_notices) > 0, "Expected infeasibility notice for conflict"


def test_presolve_single_card_exceeds_cap_returns_no_lineups():
    """A locked card whose salary alone exceeds salary_max triggers a pre-solve error."""
    over_cap = make_card("Over Cap Player", 70000, 1.0, "Core", 80.0)
    all_cards = TIPS_CARDS + [over_cap]
    key = ("Over Cap Player", 70000, 1.0, "Core")
    cs = ConstraintSet(locked_cards=[key])
    result = optimize(all_cards, TIPS_CONFIG, constraints=cs)
    for contest_lineups in result.lineups.values():
        assert contest_lineups == [], (
            f"Expected no lineups on pre-solve error, got: {contest_lineups}"
        )
    assert len(result.infeasibility_notices) > 0
    notice_text = " ".join(result.infeasibility_notices)
    assert "70,000" in notice_text or "salary" in notice_text.lower(), (
        f"Expected salary info in notice: {notice_text}"
    )


def test_infeasible_card_locks_generate_notices_but_not_block_free_lineups():
    """Card locks too expensive to fit a valid lineup generate notices; other slots still build."""
    # $40k card: needs 5 more players at ~$8k each = $80k total > $64k cap — infeasible
    card_a = make_card("Big Contract A", 40000, 1.0, "Core", 80.0)
    card_b = make_card("Big Contract B", 30000, 1.0, "Core", 75.0)
    all_cards = TIPS_CARDS + [card_a, card_b]
    key_a = ("Big Contract A", 40000, 1.0, "Core")
    key_b = ("Big Contract B", 30000, 1.0, "Core")
    cs = ConstraintSet(locked_cards=[key_a, key_b])
    result = optimize(all_cards, TIPS_CONFIG, constraints=cs)
    assert len(result.infeasibility_notices) >= 2, (
        f"Expected at least 2 infeasibility notices, got: {result.infeasibility_notices}"
    )
    assert len(result.lineups["The Tips"]) == 3, (
        "Free lineup slots should still be built when locked cards are individually infeasible"
    )


# ---------------------------------------------------------------------------
# Tests: entry_overrides (per-contest lineup count at runtime)
# ---------------------------------------------------------------------------

def test_entry_overrides_reduces_count():
    """entry_overrides limits The Tips to 1 lineup; The Intermediate Tee uses default (2)."""
    result = optimize(ALL_CARDS, ALL_CONTESTS, entry_overrides={"The Tips": 1})
    assert len(result.lineups["The Tips"]) == 1
    assert len(result.lineups["The Intermediate Tee"]) == 2


def test_entry_overrides_zero_skips_contest():
    """entry_overrides of 0 produces no lineups for that contest and no infeasibility notice."""
    result = optimize(ALL_CARDS, ALL_CONTESTS, entry_overrides={"The Tips": 0})
    assert result.lineups["The Tips"] == []
    assert not any("The Tips" in n for n in result.infeasibility_notices)


def test_entry_overrides_clamped_to_max():
    """entry_overrides above max_entries is clamped down to max_entries."""
    result = optimize(ALL_CARDS, ALL_CONTESTS, entry_overrides={"The Tips": 99})
    assert len(result.lineups["The Tips"]) == 3  # max_entries for The Tips


def test_entry_overrides_unknown_contest_ignored():
    """Override keys that don't match any contest are silently ignored; defaults apply."""
    result = optimize(ALL_CARDS, ALL_CONTESTS, entry_overrides={"Bogus Contest": 5})
    assert len(result.lineups["The Tips"]) == 3
    assert len(result.lineups["The Intermediate Tee"]) == 2


# ---------------------------------------------------------------------------
# Tests: duplicate cards (same composite key, distinct instance_id)
# ---------------------------------------------------------------------------

def _build_dup_pool():
    """A pool with one duplicated star plus enough fillers for 2 Tips lineups (12 cards)."""
    cards = [
        # Two copies of the same star card — composite key matches, instance IDs differ
        make_card("Star Player", 12000, 1.5, "Core", 80.0, instance_id=1000),
        make_card("Star Player", 12000, 1.5, "Core", 80.0, instance_id=1001),
        # 10 unique fillers spanning enough salary to clear $30K floor
        make_card("Filler 01", 9000, 1.2, "Core", 60.0),
        make_card("Filler 02", 8500, 1.1, "Core", 58.0),
        make_card("Filler 03", 8000, 1.0, "Core", 55.0),
        make_card("Filler 04", 8000, 1.0, "Core", 54.0),
        make_card("Filler 05", 8000, 1.0, "Core", 53.0),
        make_card("Filler 06", 7500, 1.0, "Core", 52.0),
        make_card("Filler 07", 9500, 1.2, "Core", 61.0),
        make_card("Filler 08", 9000, 1.1, "Core", 59.0),
        make_card("Filler 09", 8500, 1.0, "Core", 57.0),
        make_card("Filler 10", 8500, 1.0, "Core", 56.0),
    ]
    return cards


def test_duplicate_cards_used_in_separate_lineups():
    """User owns 2 copies of one card. Optimizer should use both, in different lineups."""
    cards = _build_dup_pool()
    config = [ContestConfig("The Tips", 30000, 64000, 6, 2, {"Weekly Collection": 3, "Core": 6})]
    result = optimize(cards, config)
    assert len(result.lineups["The Tips"]) == 2, (
        f"Expected 2 lineups; got {len(result.lineups['The Tips'])}. "
        f"Notices: {result.infeasibility_notices}"
    )
    used_instance_ids = [c.instance_id for lu in result.lineups["The Tips"] for c in lu.cards]
    assert 1000 in used_instance_ids, "First Star Player copy should be used"
    assert 1001 in used_instance_ids, "Second Star Player copy should be used"


def test_lock_on_duplicated_card_uses_one_instance():
    """Locking a composite key with two duplicate copies in the pool selects exactly one instance."""
    cards = _build_dup_pool()
    config = [ContestConfig("The Tips", 30000, 64000, 6, 1, {"Weekly Collection": 3, "Core": 6})]
    star_key = ("Star Player", 12000, 1.5, "Core")
    cs = ConstraintSet(locked_cards=[star_key])
    result = optimize(cards, config, constraints=cs)

    assert len(result.lineups["The Tips"]) == 1
    lineup = result.lineups["The Tips"][0]

    star_in_lineup = [c for c in lineup.cards if c.player == "Star Player"]
    assert len(star_in_lineup) == 1, (
        f"Lock should select exactly one Star Player instance, got {len(star_in_lineup)}: "
        f"{[(c.player, c.instance_id) for c in lineup.cards]}"
    )
    assert star_in_lineup[0].instance_id in (1000, 1001), (
        f"Selected instance should be one of the duplicates, got {star_in_lineup[0].instance_id}"
    )


def test_optimize_rejects_negative_instance_id():
    """The optimizer asserts every input card has instance_id >= 0."""
    bad_card = make_card("Bad", 9000, 1.0, "Core", 60.0, instance_id=-1)
    cards = TIPS_CARDS + [bad_card]
    with pytest.raises(AssertionError, match="instance_id"):
        optimize(cards, TIPS_CONFIG)


def test_phase2_lock_on_duplicated_low_ev_card():
    """Phase 2 _find_best_replacement correctly handles a locked, duplicated, low-EV card.

    Scenario:
      - Two copies of "Filler Star" share one composite key but distinct instance_ids.
      - Filler Star's EV is far below the cards Phase 1 would otherwise pick, so
        Phase 1's pure-optimal solve naturally excludes both copies.
      - Locking Filler Star's composite key forces Phase 2's _satisfy_lock path,
        which calls _find_best_replacement to swap the lock into the best slot.

    Assertions:
      1. Exactly one of the two copies ends up in some lineup (not zero, not both).
      2. The other copy is still in result.unused_cards — proves used_instance_ids
         was correctly updated by Phase 2 (no double-discard, no stale state).
    """
    cards = [
        # Two copies of the low-EV target. Same composite key, distinct instance_ids.
        make_card("Filler Star", 9000, 1.0, "Core", 50.0, instance_id=2000),
        make_card("Filler Star", 9000, 1.0, "Core", 50.0, instance_id=2001),
        # 12 high-EV unique cards that Phase 1 will prefer over Filler Star.
        # Each has projected_score 90+, so EV >> 50.
        make_card("Top 01", 9000, 1.2, "Core", 95.0),
        make_card("Top 02", 9000, 1.2, "Core", 94.0),
        make_card("Top 03", 9000, 1.2, "Core", 93.0),
        make_card("Top 04", 9000, 1.2, "Core", 92.0),
        make_card("Top 05", 9000, 1.2, "Core", 91.0),
        make_card("Top 06", 9000, 1.2, "Core", 90.0),
        make_card("Top 07", 9000, 1.1, "Core", 89.0),
        make_card("Top 08", 9000, 1.1, "Core", 88.0),
        make_card("Top 09", 9000, 1.1, "Core", 87.0),
        make_card("Top 10", 9000, 1.1, "Core", 86.0),
        make_card("Top 11", 9000, 1.1, "Core", 85.0),
        make_card("Top 12", 9000, 1.1, "Core", 84.0),
    ]
    config = [ContestConfig("The Tips", 30000, 64000, 6, 2, {"Weekly Collection": 3, "Core": 6})]
    star_key = ("Filler Star", 9000, 1.0, "Core")
    cs = ConstraintSet(locked_cards=[star_key])
    result = optimize(cards, config, constraints=cs)

    # Sanity: 2 lineups built, no infeasibility
    assert len(result.lineups["The Tips"]) == 2, (
        f"Expected 2 lineups, got {len(result.lineups['The Tips'])}. "
        f"Notices: {result.infeasibility_notices}"
    )

    # Confirm Phase 2 was actually exercised: Phase 1 alone (no locks) would never
    # pick Filler Star because its EV (50) is below every other card. So the only
    # path that gets Filler Star into a lineup is _satisfy_lock -> _find_best_replacement.
    star_instances_used = [
        c.instance_id
        for lu in result.lineups["The Tips"]
        for c in lu.cards
        if c.player == "Filler Star"
    ]

    # Assertion 1: exactly one Filler Star instance is in the lineups
    assert len(star_instances_used) == 1, (
        f"Lock should produce exactly one Filler Star instance in lineups; "
        f"got {len(star_instances_used)}: {star_instances_used}"
    )
    used_id = star_instances_used[0]
    assert used_id in (2000, 2001), f"Used instance_id {used_id} should be one of the duplicates"

    # Assertion 2 (bonus): the OTHER copy is still free for future use.
    # This proves used_instance_ids was correctly updated by Phase 2 — no
    # double-discard (which would mark both used) and no stale state.
    other_id = 2001 if used_id == 2000 else 2000
    unused_ids = {c.instance_id for c in result.unused_cards}
    assert other_id in unused_ids, (
        f"Other Filler Star instance ({other_id}) should be in unused_cards but isn't. "
        f"unused_cards instance_ids: {sorted(unused_ids)}"
    )

