import pytest


def test_valid_roster_parses_to_cards(tmp_csv_file, sample_roster_csv):
    from gbgolf.data.roster import parse_roster_csv  # ImportError until Plan 02
    path = tmp_csv_file(sample_roster_csv)
    cards = parse_roster_csv(path)
    assert len(cards) > 0


def test_missing_column_fails(tmp_csv_file):
    from gbgolf.data.roster import parse_roster_csv
    bad_csv = "Player,Salary\nScottie Scheffler,12000\n"
    path = tmp_csv_file(bad_csv)
    with pytest.raises(ValueError, match="missing required columns"):
        parse_roster_csv(path)


def test_card_fields_populated(tmp_csv_file, sample_roster_csv):
    from gbgolf.data.roster import parse_roster_csv
    path = tmp_csv_file(sample_roster_csv)
    cards = parse_roster_csv(path)
    card = cards[0]
    assert card.player == "Scottie Scheffler"
    assert card.salary == 12000
    assert card.multiplier == 1.5
    assert card.collection == "Core"


def test_instance_id_monotonic_from_row_order(tmp_csv_file, sample_roster_csv):
    """parse_roster_csv assigns instance_id sequentially from CSV row index, starting at 0."""
    from gbgolf.data.roster import parse_roster_csv
    path = tmp_csv_file(sample_roster_csv)
    cards = parse_roster_csv(path)
    ids = [c.instance_id for c in cards]
    assert ids == list(range(len(cards))), (
        f"Expected instance_ids 0..{len(cards) - 1}, got: {ids}"
    )


def test_duplicate_csv_rows_get_distinct_instance_ids(tmp_csv_file):
    """Two identical CSV rows produce two Cards with distinct instance_ids (same composite key)."""
    from gbgolf.data.roster import parse_roster_csv
    csv_text = (
        "Player,Positions,Team,Multiplier,Overall,Franchise,Rookie,Tradeable,Salary,Collection,Status,Expires\n"
        "Sam Stevens,G,USA,1.5,102,False,False,True,10950,2026 Core,Active,2026-12-31\n"
        "Sam Stevens,G,USA,1.5,102,False,False,True,10950,2026 Core,Active,2026-12-31\n"
    )
    path = tmp_csv_file(csv_text)
    cards = parse_roster_csv(path)
    assert len(cards) == 2
    assert cards[0].instance_id != cards[1].instance_id
    assert (cards[0].player, cards[0].salary, cards[0].multiplier, cards[0].collection) == \
           (cards[1].player, cards[1].salary, cards[1].multiplier, cards[1].collection)
