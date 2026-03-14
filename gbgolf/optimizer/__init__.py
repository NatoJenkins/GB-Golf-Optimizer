from dataclasses import dataclass, field
from gbgolf.data.models import Card
from gbgolf.optimizer.engine import _solve_one_lineup
from gbgolf.optimizer.constraints import ConstraintSet, check_conflicts, check_feasibility


@dataclass
class Lineup:
    """Represents a single optimized lineup for a contest."""
    contest: str
    cards: list  # list[Card]

    def __post_init__(self):
        self.total_salary: int = sum(c.salary for c in self.cards)
        self.total_projected_score: float = sum(
            (c.projected_score or 0.0) for c in self.cards
        )
        self.total_effective_value: float = sum(
            (c.effective_value or 0.0) for c in self.cards
        )


@dataclass
class OptimizationResult:
    """Result of running the optimizer across all contests."""
    lineups: dict  # dict[str, list[Lineup]]
    unused_cards: list  # list[Card]
    infeasibility_notices: list  # list[str]


def _card_key(c) -> tuple:
    """Return the composite key for a card: (player, salary, multiplier, collection)."""
    return (c.player, c.salary, c.multiplier, c.collection)


def optimize(
    valid_cards: list,
    contests: list,
    constraints: ConstraintSet | None = None,
) -> OptimizationResult:
    """Generate optimal lineups for each contest.

    For each contest, generates up to max_entries lineups by iteratively
    calling _solve_one_lineup. Cards used in previous lineups are excluded
    from the pool for subsequent lineups (disjoint card usage).

    Lock/exclude behavior (when constraints is provided):
    - check_conflicts() and check_feasibility() run before any lineup is built.
      If either fails, returns OptimizationResult with empty lineups and the
      error message in infeasibility_notices.
    - Excluded cards and excluded players are pre-filtered from the available
      pool each iteration.
    - Card locks fire once: after a locked card is placed, it's removed from
      the active lock set (the card is consumed by normal used_card_keys logic).
    - Golfer locks fire once: after a golfer is placed in any lineup, the lock
      is removed from unsatisfied_golfer_locks so subsequent lineups are not
      forced to include them (preventing infeasibility when the golfer has only
      one card).

    Args:
        valid_cards: list[Card] from the validation pipeline
        contests: list[ContestConfig] defining each contest's constraints
        constraints: ConstraintSet with lock/exclude directives, or None for
            unconstrained optimization

    Returns:
        OptimizationResult with lineups per contest and any infeasibility notices
    """
    if constraints is None:
        constraints = ConstraintSet()

    # Pre-solve conflict check (runs once before any lineup is built)
    if error := check_conflicts(constraints):
        return OptimizationResult(
            lineups={c.name: [] for c in contests},
            unused_cards=valid_cards,
            infeasibility_notices=[error.message],
        )

    # Pre-solve feasibility check per contest
    for config in contests:
        if error := check_feasibility(constraints, valid_cards, config):
            return OptimizationResult(
                lineups={c.name: [] for c in contests},
                unused_cards=valid_cards,
                infeasibility_notices=[error.message],
            )

    # Prepare exclude sets (static across all lineups)
    excluded_card_keys: set = set(constraints.excluded_cards)
    excluded_player_names: set = set(constraints.excluded_players)

    # Golfer locks: fires once globally — discard after first placement
    unsatisfied_golfer_locks: set = set(constraints.locked_golfers)

    # Card locks: fires once per card — discard after first placement
    active_card_locks: set = set(constraints.locked_cards)

    lineups: dict = {}
    infeasibility_notices: list = []
    used_card_keys: set = set()

    for config in contests:
        contest_lineups: list = []

        for entry_num in range(config.max_entries):
            # Exclude: cards already used, excluded by key, excluded by player name
            available = [
                c for c in valid_cards
                if _card_key(c) not in used_card_keys
                and _card_key(c) not in excluded_card_keys
                and c.player not in excluded_player_names
            ]

            result = _solve_one_lineup(
                available,
                config,
                locked_card_keys=active_card_locks if active_card_locks else None,
                locked_golfer_names=unsatisfied_golfer_locks if unsatisfied_golfer_locks else None,
            )

            if result is None:
                notice = (
                    f"{config.name}: lineup {entry_num + 1} of {config.max_entries} "
                    f"could not be built (infeasible)"
                )
                infeasibility_notices.append(notice)
            else:
                # Mark these cards as used (composite key deduplication)
                for card in result:
                    key = _card_key(card)
                    used_card_keys.add(key)
                    # Golfer lock fires once: discard after placement
                    unsatisfied_golfer_locks.discard(card.player)
                    # Card lock fires once: discard after placement
                    active_card_locks.discard(key)
                contest_lineups.append(Lineup(contest=config.name, cards=result))

        lineups[config.name] = contest_lineups

    unused_cards = [c for c in valid_cards if _card_key(c) not in used_card_keys]

    return OptimizationResult(
        lineups=lineups,
        unused_cards=unused_cards,
        infeasibility_notices=infeasibility_notices,
    )


__all__ = ["optimize", "OptimizationResult", "Lineup"]
