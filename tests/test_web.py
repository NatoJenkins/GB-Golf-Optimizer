"""
Integration tests for the Flask web layer (gbgolf.web).
Tests are in RED state until Task 2 implements the web package.
"""
import io
import pytest

# ---------------------------------------------------------------------------
# Sample CSV data — enough cards for both contests to generate lineups.
# The Tips: 6-card lineup, salary range 30k-64k, up to 3 entries.
# The Intermediate Tee: 5-card lineup, salary range 20k-52k, up to 2 entries.
# We need disjoint cards for all 5 lineups = 3*6 + 2*5 = 28 card slots minimum.
# We provide 30 valid cards + 1 extra for the exclusion test.
# ---------------------------------------------------------------------------

_HEADER = "Player,Positions,Team,Multiplier,Overall,Franchise,Rookie,Tradeable,Salary,Collection,Status,Expires"

def _make_card(player, salary, multiplier, collection="Core"):
    return f"{player},G,ATL,{multiplier},80,False,False,True,{salary},{collection},Active,2027-12-31"


# 30 valid players with projections — enough for disjoint lineup generation
_VALID_PLAYERS = [
    # For The Tips (salary in range 30k-64k when summed across 6 cards)
    # Each card ~5k-11k salary; 6 cards * avg 9k = 54k (in range)
    ("Player A",  11000, 1.5),
    ("Player B",  10500, 1.4),
    ("Player C",  10000, 1.3),
    ("Player D",   9500, 1.2),
    ("Player E",   9000, 1.1),
    ("Player F",   8500, 1.2),
    ("Player G",   8000, 1.1),
    ("Player H",   7500, 1.0),
    ("Player I",   7000, 1.1),
    ("Player J",   6500, 1.0),
    ("Player K",  11000, 1.4),
    ("Player L",  10000, 1.3),
    ("Player M",   9000, 1.2),
    ("Player N",   8000, 1.1),
    ("Player O",   7000, 1.0),
    ("Player P",   6500, 1.1),
    ("Player Q",  10500, 1.3),
    ("Player R",   9500, 1.2),
    ("Player S",   8500, 1.1),
    ("Player T",   7500, 1.0),
    ("Player U",   6000, 1.2),
    ("Player V",   5500, 1.1),
    ("Player W",   5000, 1.0),
    ("Player X",   4500, 1.1),
    ("Player Y",  11000, 1.5),
    ("Player Z",  10000, 1.4),
    ("Player AA",  9000, 1.3),
    ("Player AB",  8000, 1.2),
    ("Player AC",  7000, 1.1),
    ("Player AD",  6000, 1.0),
]

_roster_rows = [_make_card(p, s, m) for p, s, m in _VALID_PLAYERS]

# SAMPLE_ROSTER_CSV: all 30 valid players
SAMPLE_ROSTER_CSV = _HEADER + "\n" + "\n".join(_roster_rows) + "\n"

# SAMPLE_PROJECTIONS_CSV: matching projections for all 30 valid players
_proj_rows = [f"{p},72.5" for p, _, _ in _VALID_PLAYERS]
SAMPLE_PROJECTIONS_CSV = "player,projected_score\n" + "\n".join(_proj_rows) + "\n"

# EXCLUSION_ROSTER_CSV: 30 valid players + 1 player with no matching projection
EXCLUSION_ROSTER_CSV = (
    SAMPLE_ROSTER_CSV.rstrip("\n")
    + "\nUnmatched Player,G,ATL,1.0,75,False,False,True,5000,Core,Active,2027-12-31\n"
)
# EXCLUSION_PROJECTIONS_CSV is the same as SAMPLE_PROJECTIONS_CSV (Unmatched Player has no projection)
EXCLUSION_PROJECTIONS_CSV = SAMPLE_PROJECTIONS_CSV

# TINY_ROSTER_CSV: only 1 card — will fail validate_pipeline pool-size guard
TINY_ROSTER_CSV = _HEADER + "\n" + _make_card("Solo Player", 5000, 1.0) + "\n"
TINY_PROJECTIONS_CSV = "player,projected_score\nSolo Player,55.0\n"


def _post_csvs(client, roster_csv, projections_csv):
    """Helper: POST two CSVs to the index route and return the response."""
    return client.post(
        "/",
        data={
            "roster": (io.BytesIO(roster_csv.encode("utf-8")), "roster.csv"),
            "projections": (io.BytesIO(projections_csv.encode("utf-8")), "projections.csv"),
        },
        content_type="multipart/form-data",
    )


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    from gbgolf.web import create_app  # ImportError until Task 2
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_lineup_table_columns(client):
    """HTML response contains expected column headers."""
    response = _post_csvs(client, SAMPLE_ROSTER_CSV, SAMPLE_PROJECTIONS_CSV)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "<th>Player</th>" in html
    assert "<th>Collection</th>" in html
    assert "<th>Salary</th>" in html
    assert "<th>Multiplier</th>" in html
    assert "<th>Proj Score</th>" in html


def test_lineup_totals_row(client):
    """HTML response contains tfoot element (totals row)."""
    response = _post_csvs(client, SAMPLE_ROSTER_CSV, SAMPLE_PROJECTIONS_CSV)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "<tfoot>" in html


def test_contest_sections_order(client):
    """The Tips section appears before The Intermediate Tee section."""
    response = _post_csvs(client, SAMPLE_ROSTER_CSV, SAMPLE_PROJECTIONS_CSV)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    tips_idx = html.index("The Tips")
    tee_idx = html.index("The Intermediate Tee")
    assert tips_idx < tee_idx, "The Tips must appear before The Intermediate Tee"


def test_lineups_grouped_by_contest(client):
    """Both contest sections appear in the response HTML."""
    response = _post_csvs(client, SAMPLE_ROSTER_CSV, SAMPLE_PROJECTIONS_CSV)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "The Tips" in html
    assert "The Intermediate Tee" in html


def test_infeasibility_notice_rendered(client):
    """Posting a tiny card pool triggers an infeasibility message."""
    response = _post_csvs(client, TINY_ROSTER_CSV, TINY_PROJECTIONS_CSV)
    # validate_pipeline raises ValueError for pool too small — expect error rendered
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    # Either a ValueError message or "could not be built" / "infeasible"
    assert (
        "could not be built" in html
        or "infeasible" in html
        or "Check your exclusion report" in html
        or "valid card" in html
    )


def test_exclusion_report_hidden_on_clean_run(client):
    """Exclusion report section is NOT present when all cards have projections."""
    response = _post_csvs(client, SAMPLE_ROSTER_CSV, SAMPLE_PROJECTIONS_CSV)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "exclusion-report" not in html


def test_exclusion_report_content(client):
    """Exclusion report shows player name and reason when a card is excluded."""
    response = _post_csvs(client, EXCLUSION_ROSTER_CSV, EXCLUSION_PROJECTIONS_CSV)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Unmatched Player" in html
    assert "no projection found" in html


def test_session_cleared_on_upload(client):
    """POST with files clears lock/exclude session keys unconditionally."""
    with client.session_transaction() as sess:
        sess["locked_cards"] = [["Player A", 11000, 1.5, "Core"]]
        sess["locked_golfers"] = ["Player A"]
    response = _post_csvs(client, SAMPLE_ROSTER_CSV, SAMPLE_PROJECTIONS_CSV)
    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert "locked_cards" not in sess or sess.get("locked_cards") == []
        assert "locked_golfers" not in sess or sess.get("locked_golfers") == []


def test_reset_banner_shown(client):
    """After a file-upload POST, the reset banner appears in the HTML response."""
    response = _post_csvs(client, SAMPLE_ROSTER_CSV, SAMPLE_PROJECTIONS_CSV)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Locks and excludes reset" in html


def test_no_reset_banner_on_get(client):
    """GET request to index does not show the reset banner."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Locks and excludes reset" not in html
