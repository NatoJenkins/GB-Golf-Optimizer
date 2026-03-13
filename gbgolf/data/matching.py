import unicodedata
from gbgolf.data.models import Card


def normalize_name(name: str) -> str:
    """
    Normalize a player name for matching:
    1. Strip leading/trailing whitespace
    2. Lowercase
    3. NFKD decomposition + drop combining marks (handles Åberg -> aberg)

    Per locked decision: no punctuation stripping.
    NFKD accent handling is within Claude's Discretion for edge cases
    per CONTEXT.md — handles golfers like Ludvig Åberg, Nicolai Højgaard.
    """
    name = name.strip().lower()
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    return name


def match_projections(
    cards: list[Card], projections: dict[str, float]
) -> list[Card]:
    """
    Enrich each Card with projected_score and effective_value from projections dict.
    projections keys must already be normalized (output of parse_projections_csv).
    Unmatched cards get projected_score=None, effective_value=None.
    """
    for card in cards:
        key = normalize_name(card.player)
        if key in projections:
            card.projected_score = projections[key]
            card.effective_value = round(card.projected_score * card.multiplier, 4)
    return cards
