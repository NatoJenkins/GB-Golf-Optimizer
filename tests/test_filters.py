import pytest
from datetime import date


def test_zero_salary_excluded(tmp_csv_file, sample_roster_csv, sample_projections_csv):
    from gbgolf.data.filters import apply_filters  # ImportError until Plan 02
    from gbgolf.data.models import Card, ExclusionRecord
    cards = [Card(player="Zero Guy", salary=0, multiplier=1.0, collection="Core",
                  expires=None, instance_id=0,
                  projected_score=60.0, effective_value=60.0)]
    valid, excluded = apply_filters(cards)
    assert len(valid) == 0
    assert any(r.reason == "$0 salary" for r in excluded)


def test_no_projection_excluded():
    from gbgolf.data.filters import apply_filters
    from gbgolf.data.models import Card
    cards = [Card(player="Ghost Player", salary=8000, multiplier=1.2, collection="Core",
                  expires=None, instance_id=0,
                  projected_score=None, effective_value=None)]
    valid, excluded = apply_filters(cards)
    assert len(valid) == 0
    assert any(r.reason == "no projection found" for r in excluded)


def test_unmatched_name_in_report():
    from gbgolf.data.filters import apply_filters
    from gbgolf.data.models import Card
    cards = [Card(player="Exact Name Here", salary=8000, multiplier=1.2, collection="Core",
                  expires=None, instance_id=0,
                  projected_score=None, effective_value=None)]
    _, excluded = apply_filters(cards)
    assert excluded[0].player == "Exact Name Here"


def test_expired_excluded():
    from gbgolf.data.filters import apply_filters
    from gbgolf.data.models import Card
    past_date = date(2020, 1, 1)
    cards = [Card(player="Old Card", salary=8000, multiplier=1.2, collection="Core",
                  expires=past_date, instance_id=0,
                  projected_score=60.0, effective_value=72.0)]
    valid, excluded = apply_filters(cards)
    assert len(valid) == 0
    assert any(r.reason == "expired card" for r in excluded)


def test_expires_today_included():
    from gbgolf.data.filters import apply_filters
    from gbgolf.data.models import Card
    cards = [Card(player="Today Card", salary=8000, multiplier=1.2, collection="Core",
                  expires=date.today(), instance_id=0,
                  projected_score=60.0, effective_value=72.0)]
    valid, excluded = apply_filters(cards)
    assert len(valid) == 1  # today is NOT expired
    assert len(excluded) == 0
