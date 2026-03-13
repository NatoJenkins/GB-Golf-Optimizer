from gbgolf.data.models import Card, ExclusionRecord, ValidationResult


def format_summary(result: ValidationResult, total_parsed: int) -> str:
    """Return one-line summary string."""
    return (
        f"Parsed: {total_parsed} cards | "
        f"Valid: {len(result.valid_cards)} | "
        f"Excluded: {len(result.excluded)}"
    )


def format_exclusion_report(excluded: list[ExclusionRecord]) -> str:
    """Return formatted exclusion list, one entry per line."""
    if not excluded:
        return "  (none)"
    lines = [f"  [{r.reason}] {r.player}" for r in excluded]
    return "\n".join(lines)


def format_verbose(valid_cards: list[Card]) -> str:
    """Return table of valid cards with effective values."""
    if not valid_cards:
        return "  (no valid cards)"
    lines = []
    for c in sorted(valid_cards, key=lambda x: -(x.effective_value or 0)):
        eff = f"{c.effective_value:.2f}" if c.effective_value is not None else "n/a"
        lines.append(
            f"  {c.player} | {c.collection} | ${c.salary:,} | "
            f"x{c.multiplier} | eff: {eff}"
        )
    return "\n".join(lines)
