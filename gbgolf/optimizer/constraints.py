"""Constraint data structures and pre-solve diagnostic functions.

Usage order: check_conflicts() must always be called before check_feasibility()
in callers, because conflict errors (lock + exclude same card) are logically
prior to feasibility errors (locked salary exceeds cap).

ConstraintSet encodes all user-specified lock and exclude directives.
PreSolveError is returned when a constraint combination is provably infeasible
before the ILP solver is invoked.

Note on golfer locks: locked_golfers is enforced as an ILP constraint in
engine.py (at least one card per golfer per lineup). It is NOT checked in
check_feasibility because golfer availability depends on the runtime card pool.

Note on excludes: excluded_cards and excluded_players are applied as pre-filters
in optimize() (engine pre-filter). They are NOT checked in check_feasibility.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from gbgolf.data.config import ContestConfig

# CardKey: (player: str, salary: int, multiplier: float, collection: str)
CardKey = tuple


@dataclass
class ConstraintSet:
    """User-specified lock/exclude directives for the optimizer.

    All fields default to empty list — callers can construct ConstraintSet()
    with no arguments to get a no-op constraint set.

    Fields:
        locked_cards: composite keys of cards that must appear in the lineup
        locked_golfers: player names where at least one card must appear
        excluded_cards: composite keys of cards that must NOT appear
        excluded_players: player names whose cards must NOT appear
    """
    locked_cards: list[CardKey] = field(default_factory=list)
    locked_golfers: list[str] = field(default_factory=list)
    excluded_cards: list[CardKey] = field(default_factory=list)
    excluded_players: list[str] = field(default_factory=list)


@dataclass
class PreSolveError:
    """Diagnostic returned when constraints are provably infeasible before solving.

    Callers should surface error.message to the user and skip the ILP solve.
    """
    message: str


def check_conflicts(constraints: ConstraintSet) -> PreSolveError | None:
    """Detect lock/exclude conflicts that make optimization logically impossible.

    A conflict occurs when a card key appears in both locked_cards and
    excluded_cards, or a player name appears in both locked_golfers and
    excluded_players.

    Call this before check_feasibility — conflicts are logically prior.

    Args:
        constraints: ConstraintSet from the user session

    Returns:
        PreSolveError if any lock/exclude conflict exists, else None.
    """
    # Card-level conflict: same composite key locked and excluded
    locked_card_set = set(constraints.locked_cards)
    excluded_card_set = set(constraints.excluded_cards)
    card_conflicts = locked_card_set & excluded_card_set
    if card_conflicts:
        conflicting_players = {key[0] for key in card_conflicts}
        names = ", ".join(sorted(conflicting_players))
        return PreSolveError(
            message=(
                f"Conflict: {names} cannot be both locked and excluded. "
                "Remove the lock or the exclusion to proceed."
            )
        )

    # Golfer-level conflict: same player name locked and excluded
    locked_golfer_set = set(constraints.locked_golfers)
    excluded_player_set = set(constraints.excluded_players)
    golfer_conflicts = locked_golfer_set & excluded_player_set
    if golfer_conflicts:
        names = ", ".join(sorted(golfer_conflicts))
        return PreSolveError(
            message=(
                f"Conflict: {names} cannot be both locked and excluded. "
                "Remove the lock or the exclusion to proceed."
            )
        )

    return None


def check_feasibility(
    constraints: ConstraintSet,
    valid_cards: list,
    config: ContestConfig,
) -> PreSolveError | None:
    """Check whether any individual locked card exceeds the salary cap.

    Only inspects locked_cards (card-level locks). Each locked card is placed
    in its own optimal lineup slot, so aggregate salary checks across multiple
    locked cards are not applicable. The only provably infeasible case before
    solving is a single card whose salary already exceeds the salary cap.

    Golfer locks, excludes, and player-level excludes are handled by the
    engine at solve time.

    Silently ignores locked card keys that are not present in valid_cards
    (they will simply not fire in the ILP).

    Call check_conflicts() first — this function assumes no lock/exclude
    conflicts exist.

    Args:
        constraints: ConstraintSet from the user session
        valid_cards: list[Card] — the validated card pool
        config: ContestConfig — salary bounds and collection limits

    Returns:
        PreSolveError if a locked card's salary exceeds the cap, else None.
    """
    card_map = {
        (c.player, c.salary, c.multiplier, c.collection): c
        for c in valid_cards
    }

    locked = [card_map[k] for k in constraints.locked_cards if k in card_map]

    for c in locked:
        if c.salary > config.salary_max:
            return PreSolveError(
                message=(
                    f"Locked card for {c.player} costs ${c.salary:,}, which "
                    f"exceeds the salary cap of ${config.salary_max:,}. "
                    "Remove the lock or choose a cheaper card to proceed."
                )
            )

    return None


__all__ = [
    "ConstraintSet",
    "PreSolveError",
    "check_conflicts",
    "check_feasibility",
    "CardKey",
]
