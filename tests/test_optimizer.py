"""Failing test stubs for the optimizer module (RED baseline).

Each test calls optimize() which raises NotImplementedError — this causes
each test to fail with an ERROR status (not a collection failure). This is
the expected RED state for TDD. Do NOT suppress the NotImplementedError.
"""
from datetime import date
from gbgolf.data.models import Card
from gbgolf.data.config import ContestConfig
from gbgolf.optimizer import optimize, OptimizationResult, Lineup


# ---------------------------------------------------------------------------
# Card builder helper
# ---------------------------------------------------------------------------

def make_card(player, salary, multiplier, collection, projected_score, effective_value=None):
    ev = effective_value if effective_value is not None else round(projected_score * multiplier, 4)
    return Card(
        player=player,
        salary=salary,
        multiplier=multiplier,
        collection=collection,
        expires=date(2026, 12, 31),
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

# 25 unique cards for multi-contest tests (disjoint card pools needed)
ALL_CARDS = [
    make_card(f"Player {i:02d}", 8000 + (i * 200), 1.0 + (i * 0.05), "Core", 55.0 + i)
    for i in range(20)
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
    """Card ids used in Tips lineups are disjoint from card ids used in Intermediate Tee lineups."""
    result = optimize(ALL_CARDS, ALL_CONTESTS)
    tips_ids = {
        id(card)
        for lineup in result.lineups.get("The Tips", [])
        for card in lineup.cards
    }
    inter_ids = {
        id(card)
        for lineup in result.lineups.get("The Intermediate Tee", [])
        for card in lineup.cards
    }
    overlap = tips_ids & inter_ids
    assert not overlap, f"Cards reused across contests: {len(overlap)} card(s)"


def test_card_uniqueness_all_lineups():
    """No card (by id()) appears in more than one lineup across all contests."""
    result = optimize(ALL_CARDS, ALL_CONTESTS)
    seen_ids: set = set()
    for contest_name, lineups in result.lineups.items():
        for lineup in lineups:
            for card in lineup.cards:
                card_id = id(card)
                assert card_id not in seen_ids, (
                    f"Card '{card.player}' reused in {contest_name}"
                )
                seen_ids.add(card_id)


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
