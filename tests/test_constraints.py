"""Unit tests for ConstraintSet and pre-solve diagnostics (TDD RED baseline).

These tests validate the constraint contract defined in gbgolf/optimizer/constraints.py.
Covers requirements: LOCK-01, LOCK-02, LOCK-03, LOCK-04, EXCL-01, EXCL-02.

Run order: check_conflicts must always run before check_feasibility.
"""
from datetime import date

from gbgolf.data.config import ContestConfig
from gbgolf.data.models import Card
from gbgolf.optimizer.constraints import (
    ConstraintSet,
    PreSolveError,
    check_conflicts,
    check_feasibility,
)


# ---------------------------------------------------------------------------
# Card builder helper (same pattern as test_optimizer.py)
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
# Module-level fixtures
# ---------------------------------------------------------------------------

TIPS_CONFIG = ContestConfig(
    name="The Tips",
    salary_min=30000,
    salary_max=64000,
    roster_size=6,
    max_entries=3,
    collection_limits={"Weekly Collection": 3, "Core": 6},
)

EMPTY_CONSTRAINTS = ConstraintSet()

# Pre-built cards for reuse in tests
SCHEFFLER_CARD = make_card("Scottie Scheffler", 12000, 1.5, "Core", 72.5)
RORY_CARD = make_card("Rory McIlroy", 11000, 1.2, "Weekly Collection", 68.3)


# ---------------------------------------------------------------------------
# Tests: ConstraintSet default state
# ---------------------------------------------------------------------------

def test_constraint_set_empty_default():
    """ConstraintSet() creates instance with all lists empty."""
    cs = ConstraintSet()
    assert cs.locked_cards == []
    assert cs.locked_golfers == []
    assert cs.excluded_cards == []
    assert cs.excluded_players == []


# ---------------------------------------------------------------------------
# Tests: Card lock (LOCK-01)
# ---------------------------------------------------------------------------

def test_card_lock_places_card():
    """A locked card key passes both check_conflicts and check_feasibility with no error."""
    scheffler_key = ("Scottie Scheffler", 12000, 1.5, "Core")
    cs = ConstraintSet(locked_cards=[scheffler_key])
    assert check_conflicts(cs) is None
    assert check_feasibility(cs, [SCHEFFLER_CARD], TIPS_CONFIG) is None


def test_card_lock_missing_card():
    """LOCK-01 edge case: locked key not present in pool is silently skipped (no salary to sum)."""
    ghost_key = ("Ghost Player", 9000, 1.0, "Core")
    cs = ConstraintSet(locked_cards=[ghost_key])
    # Empty pool — ghost key not found, no salary check fires
    result = check_feasibility(cs, [], TIPS_CONFIG)
    assert result is None


# ---------------------------------------------------------------------------
# Tests: Golfer lock (LOCK-02)
# ---------------------------------------------------------------------------

def test_golfer_lock_satisfied():
    """Golfer lock is an ILP constraint, not a pre-solve check; returns None from both functions."""
    cs = ConstraintSet(locked_golfers=["Scottie Scheffler"])
    assert check_conflicts(cs) is None
    assert check_feasibility(cs, [SCHEFFLER_CARD], TIPS_CONFIG) is None


def test_golfer_lock_fires_once():
    """LOCK-02 semantic: ConstraintSet stores locked_golfers as a list of strings."""
    cs = ConstraintSet(locked_golfers=["Tiger Woods"])
    assert cs.locked_golfers == ["Tiger Woods"]


# ---------------------------------------------------------------------------
# Tests: Pre-solve salary/collection feasibility (LOCK-03)
# ---------------------------------------------------------------------------

def test_presolve_single_card_exceeds_cap():
    """LOCK-03: a single locked card whose salary > salary_max returns PreSolveError."""
    over_cap = make_card("Over Cap Player", 70000, 1.0, "Core", 80.0)
    key = ("Over Cap Player", 70000, 1.0, "Core")
    cs = ConstraintSet(locked_cards=[key])
    result = check_feasibility(cs, [over_cap], TIPS_CONFIG)
    assert isinstance(result, PreSolveError)
    assert "70,000" in result.message
    assert "64,000" in result.message


def test_presolve_aggregate_salary_not_flagged():
    """LOCK-03: two locked cards whose salaries sum above cap are not a pre-solve error.

    Each card gets its own lineup slot, so aggregate salary is not a constraint.
    The ILP solver handles infeasibility at solve time if needed.
    """
    card_a = make_card("Big Earner A", 40000, 1.0, "Core", 70.0)
    card_b = make_card("Big Earner B", 30000, 1.0, "Core", 68.0)
    key_a = ("Big Earner A", 40000, 1.0, "Core")
    key_b = ("Big Earner B", 30000, 1.0, "Core")
    cs = ConstraintSet(locked_cards=[key_a, key_b])
    result = check_feasibility(cs, [card_a, card_b], TIPS_CONFIG)
    assert result is None  # not a pre-solve error; handled by the ILP solver


def test_presolve_message_content():
    """LOCK-03: salary-exceeded error message is a non-empty string containing '$'."""
    over_cap = make_card("Over Cap Player", 70000, 1.0, "Core", 80.0)
    key = ("Over Cap Player", 70000, 1.0, "Core")
    cs = ConstraintSet(locked_cards=[key])
    result = check_feasibility(cs, [over_cap], TIPS_CONFIG)
    assert isinstance(result, PreSolveError)
    assert result.message
    assert "$" in result.message


# ---------------------------------------------------------------------------
# Tests: Conflict detection (LOCK-04)
# ---------------------------------------------------------------------------

def test_conflict_card_lock_exclude():
    """LOCK-04: same key in locked_cards and excluded_cards triggers PreSolveError."""
    key = ("Scottie Scheffler", 12000, 1.5, "Core")
    cs = ConstraintSet(locked_cards=[key], excluded_cards=[key])
    result = check_conflicts(cs)
    assert isinstance(result, PreSolveError)
    assert "Scottie Scheffler" in result.message


def test_conflict_golfer_lock_exclude():
    """LOCK-04: same player name in locked_golfers and excluded_players triggers PreSolveError."""
    cs = ConstraintSet(locked_golfers=["Rory McIlroy"], excluded_players=["Rory McIlroy"])
    result = check_conflicts(cs)
    assert isinstance(result, PreSolveError)
    assert "Rory McIlroy" in result.message


# ---------------------------------------------------------------------------
# Tests: Card exclude (EXCL-01)
# ---------------------------------------------------------------------------

def test_card_exclude_removes_card():
    """EXCL-01: excluded card produces no pre-solve error; exclusion is engine-level."""
    key = ("Rory McIlroy", 11000, 1.2, "Weekly Collection")
    cs = ConstraintSet(excluded_cards=[key])
    # No lock conflicts
    assert check_conflicts(cs) is None
    # Exclusion is not a pre-solve feasibility check
    assert check_feasibility(cs, [], TIPS_CONFIG) is None
    # Stored correctly
    assert cs.excluded_cards == [key]


# ---------------------------------------------------------------------------
# Tests: Golfer exclude (EXCL-02)
# ---------------------------------------------------------------------------

def test_golfer_exclude_removes_all_cards():
    """EXCL-02: excluded player name stored; no pre-solve error generated."""
    cs = ConstraintSet(excluded_players=["Tiger Woods"])
    assert check_conflicts(cs) is None
    assert cs.excluded_players == ["Tiger Woods"]
