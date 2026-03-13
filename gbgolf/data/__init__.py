"""
GB Golf Optimizer data layer.
Public API: validate_pipeline(), load_cards(), load_config()
"""
from gbgolf.data.config import load_contest_config, ContestConfig
from gbgolf.data.filters import apply_filters
from gbgolf.data.matching import match_projections, normalize_name
from gbgolf.data.models import Card, ExclusionRecord, ValidationResult
from gbgolf.data.projections import parse_projections_csv
from gbgolf.data.roster import parse_roster_csv


def load_cards(roster_path: str, projections_path: str) -> tuple[list[Card], list[str]]:
    """
    Parse and enrich cards from CSV files.
    Returns (enriched_cards, projection_warnings).
    enriched_cards have projected_score and effective_value set (or None if unmatched).
    """
    cards = parse_roster_csv(roster_path)
    projections, warnings = parse_projections_csv(projections_path)
    enriched = match_projections(cards, projections)
    return enriched, warnings


def load_config(config_path: str) -> list[ContestConfig]:
    """Load and validate contest config JSON. Returns list of ContestConfig."""
    return load_contest_config(config_path)


def validate_pipeline(
    roster_path: str,
    projections_path: str,
    config_path: str,
) -> ValidationResult:
    """
    Full validation pipeline: parse -> enrich -> filter.
    Raises ValueError if the valid card pool is too small for the smallest contest.
    """
    enriched, warnings = load_cards(roster_path, projections_path)
    contests = load_config(config_path)

    valid_cards, excluded = apply_filters(enriched)

    # Guard: fail before Phase 2 receives an unusable pool
    if contests:
        min_required = min(c.roster_size for c in contests)
        if len(valid_cards) < min_required:
            raise ValueError(
                f"Only {len(valid_cards)} valid card(s) found — "
                f"smallest contest requires at least {min_required}. "
                f"Check your exclusion report."
            )

    return ValidationResult(
        valid_cards=valid_cards,
        excluded=excluded,
        projection_warnings=warnings,
    )


__all__ = [
    "validate_pipeline",
    "load_cards",
    "load_config",
    "Card",
    "ContestConfig",
    "ExclusionRecord",
    "ValidationResult",
    "normalize_name",
]
