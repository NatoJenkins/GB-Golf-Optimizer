from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Card:
    """Represents one GameBlazers player card."""
    player: str
    salary: int          # Parse as int — GameBlazers salaries are whole dollars
    multiplier: float
    collection: str      # e.g. "Core", "Weekly Collection"
    expires: Optional[date]
    projected_score: Optional[float] = None
    effective_value: Optional[float] = None  # projected_score * multiplier
    # Preserved as-is from CSV — Phase 2 will interpret these if needed
    franchise: str = ""
    rookie: str = ""


@dataclass
class ExclusionRecord:
    """Records a card excluded from the optimizer pool."""
    player: str
    # One of three canonical reasons:
    reason: str  # "$0 salary" | "no projection found" | "expired card"


@dataclass
class ValidationResult:
    """Output of the full validation pipeline."""
    valid_cards: list = field(default_factory=list)
    excluded: list = field(default_factory=list)
    projection_warnings: list = field(default_factory=list)
