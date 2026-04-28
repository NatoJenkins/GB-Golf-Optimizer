from dataclasses import dataclass, field
from gbgolf.data.models import Card
from gbgolf.optimizer.engine import _solve_one_lineup
from gbgolf.optimizer.constraints import ConstraintSet, check_conflicts, check_feasibility
from gbgolf.data.config import ContestConfig


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


def _find_best_replacement(
    contest_lineups: list,
    valid_cards: list,
    used_card_keys: set,
    excluded_card_keys: set,
    excluded_player_names: set,
    config: ContestConfig,
    locked_card_keys: set | None = None,
    locked_golfer_names: set | None = None,
) -> tuple[int, list | None]:
    """Find the lineup slot where forcing a lock produces the highest projected score.

    For each existing lineup, temporarily reclaims its cards back into the pool,
    solves with the lock constraint, and records the resulting lineup's total
    effective value. Returns the index and cards of the best replacement found,
    or (-1, None) if no lineup slot can accommodate the lock.

    The used_card_keys set is temporarily mutated during the search but is
    fully restored before returning.
    """
    best_ev = -1.0
    best_idx = -1
    best_result = None

    for i, lineup in enumerate(contest_lineups):
        # Temporarily return this lineup's cards to the available pool
        for card in lineup.cards:
            used_card_keys.discard(_card_key(card))

        available = [
            c for c in valid_cards
            if _card_key(c) not in used_card_keys
            and _card_key(c) not in excluded_card_keys
            and c.player not in excluded_player_names
        ]

        result = _solve_one_lineup(
            available, config,
            locked_card_keys=locked_card_keys,
            locked_golfer_names=locked_golfer_names,
        )

        if result is not None:
            ev = sum(c.effective_value or 0.0 for c in result)
            if ev > best_ev:
                best_ev = ev
                best_idx = i
                best_result = result

        # Restore this lineup's cards before trying the next slot
        for card in lineup.cards:
            used_card_keys.add(_card_key(card))

    return best_idx, best_result


def optimize(
    valid_cards: list,
    contests: list,
    constraints: ConstraintSet | None = None,
    entry_overrides: dict | None = None,
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
    - Phase 1 generates all lineups with NO lock constraints (pure optimal).
      Locks that happen to be satisfied naturally require no further action.
    - Phase 2 processes any locks not satisfied in Phase 1. For each such lock,
      every existing lineup slot is tried as a candidate replacement: the lineup
      is temporarily reclaimed, a lock-constrained solve is run, and the slot
      that produces the highest projected score wins. This ensures each lock is
      placed where it contributes most to lineup quality rather than being
      forced into the first lineup alongside all other locks.
    - A lock fires exactly once (minimum one appearance). Subsequent lineups are
      unconstrained and may include locked players again if optimal.

    Args:
        valid_cards: list[Card] from the validation pipeline
        contests: list[ContestConfig] defining each contest's constraints
        constraints: ConstraintSet with lock/exclude directives, or None for
            unconstrained optimization
        entry_overrides: optional dict[str, int] mapping contest name to the
            desired number of lineups for that contest. Values are clamped to
            [0, config.max_entries]. Keys not matching any contest are silently
            ignored. When None or a contest has no override, config.max_entries
            is used (current default behavior).

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

    lineups: dict = {}
    infeasibility_notices: list = []
    used_card_keys: set = set()

    for config in contests:
        contest_lineups: list = []

        requested = (
            entry_overrides.get(config.name, config.max_entries)
            if entry_overrides else config.max_entries
        )
        n_entries = max(0, min(requested, config.max_entries))

        # Phase 1: generate all lineups with no lock constraints (pure optimal)
        for entry_num in range(n_entries):
            available = [
                c for c in valid_cards
                if _card_key(c) not in used_card_keys
                and _card_key(c) not in excluded_card_keys
                and c.player not in excluded_player_names
            ]
            result = _solve_one_lineup(available, config)
            if result is None:
                slot = len(contest_lineups) + 1
                infeasibility_notices.append(
                    f"{config.name}: lineup {slot} of {n_entries} "
                    f"could not be built (infeasible)"
                )
            else:
                for card in result:
                    used_card_keys.add(_card_key(card))
                contest_lineups.append(Lineup(contest=config.name, cards=result))

        # Phase 2: satisfy any locks not naturally placed in Phase 1.
        # For each unsatisfied lock, find the lineup slot where forcing the lock
        # yields the highest total projected score, then replace that slot.
        def _satisfy_lock(locked_card_keys=None, locked_golfer_names=None, label=""):
            if not contest_lineups:
                infeasibility_notices.append(
                    f"{config.name}: could not satisfy {label} (no lineups available)"
                )
                return
            idx, best_result = _find_best_replacement(
                contest_lineups, valid_cards, used_card_keys,
                excluded_card_keys, excluded_player_names, config,
                locked_card_keys=locked_card_keys,
                locked_golfer_names=locked_golfer_names,
            )
            if best_result is None:
                infeasibility_notices.append(
                    f"{config.name}: could not build lineup with {label} (infeasible)"
                )
                return
            # Replace the chosen lineup slot with the lock-constrained result
            old_lineup = contest_lineups[idx]
            for card in old_lineup.cards:
                used_card_keys.discard(_card_key(card))
            for card in best_result:
                used_card_keys.add(_card_key(card))
            contest_lineups[idx] = Lineup(contest=config.name, cards=best_result)

        for card_key in constraints.locked_cards:
            if any(_card_key(c) == card_key for lu in contest_lineups for c in lu.cards):
                continue  # already satisfied naturally
            _satisfy_lock(locked_card_keys={card_key}, label=f"locked card for '{card_key[0]}'")

        for golfer_name in constraints.locked_golfers:
            if any(c.player == golfer_name for lu in contest_lineups for c in lu.cards):
                continue  # already satisfied naturally
            _satisfy_lock(locked_golfer_names={golfer_name}, label=f"locked golfer '{golfer_name}'")

        lineups[config.name] = contest_lineups

    unused_cards = [c for c in valid_cards if _card_key(c) not in used_card_keys]

    return OptimizationResult(
        lineups=lineups,
        unused_cards=unused_cards,
        infeasibility_notices=infeasibility_notices,
    )


__all__ = ["optimize", "OptimizationResult", "Lineup"]
