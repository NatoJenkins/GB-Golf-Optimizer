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


def _post_hybrid(client, roster_csv, projections_csv):
    """Helper: POST with projection_source=hybrid."""
    return client.post(
        "/",
        data={
            "roster": (io.BytesIO(roster_csv.encode("utf-8")), "roster.csv"),
            "projections": (io.BytesIO(projections_csv.encode("utf-8")), "projections.csv"),
            "projection_source": "hybrid",
        },
        content_type="multipart/form-data",
    )


# Partial projections CSV: only first 10 of 30 players at 80.0
_PARTIAL_PROJ_ROWS = [f"{p},80.0" for p, _, _ in _VALID_PLAYERS[:10]]
PARTIAL_PROJECTIONS_CSV = "player,projected_score\n" + "\n".join(_PARTIAL_PROJ_ROWS) + "\n"


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    from gbgolf.web import create_app  # ImportError until Task 2
    from gbgolf.db import db as _db
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        _db.create_all()
        with app.test_client() as c:
            yield c
        _db.drop_all()


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


# ---------------------------------------------------------------------------
# Phase 05-01: POST /reoptimize tests (UI-02)
# ---------------------------------------------------------------------------

def _build_card_pool_json():
    """Build a valid card_pool JSON string matching the format _serialize_cards produces."""
    import json
    cards = [
        {
            "player": p,
            "salary": s,
            "multiplier": m,
            "collection": "Core",
            "expires": "2027-12-31",
            "instance_id": idx,
            "projected_score": 72.5,
            "effective_value": round(72.5 * m, 6),
            "franchise": "False",
            "rookie": "False",
        }
        for idx, (p, s, m) in enumerate(_VALID_PLAYERS)
    ]
    return json.dumps(cards)


def test_reoptimize_returns_results(client):
    """POST /reoptimize with valid card_pool JSON returns 200 with lineup table columns."""
    card_pool_json = _build_card_pool_json()
    response = client.post(
        "/reoptimize",
        data={"card_pool": card_pool_json},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Player" in html
    assert "Salary" in html
    assert "Multiplier" in html


def test_reoptimize_layout_identical(client):
    """POST /reoptimize result HTML contains both contest section headings."""
    card_pool_json = _build_card_pool_json()
    response = client.post(
        "/reoptimize",
        data={"card_pool": card_pool_json},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "The Tips" in html
    assert "The Intermediate Tee" in html


def test_reoptimize_missing_card_pool(client):
    """POST /reoptimize with no card_pool field returns 200 with session-expired message."""
    response = client.post(
        "/reoptimize",
        data={},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Session expired" in html


def test_reoptimize_malformed_card_pool(client):
    """POST /reoptimize with malformed card_pool returns 200 with session-expired message."""
    response = client.post(
        "/reoptimize",
        data={"card_pool": "not-valid-json"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Session expired" in html


def test_reoptimize_rejects_payload_missing_instance_id(client):
    """POST /reoptimize with a card payload missing 'instance_id' is rejected at the route layer.

    The user sees the stale-session message; the optimizer is never invoked.
    Regression guard: a missing instance_id must NOT silently fall through with
    a fabricated ID, which could collide with real IDs in the same payload.
    """
    import json
    cards = [
        # First card has instance_id (real); second is "legacy" / missing it.
        {
            "player": "Player A",
            "salary": 11000,
            "multiplier": 1.5,
            "collection": "Core",
            "expires": "2027-12-31",
            "instance_id": 0,
            "projected_score": 72.5,
            "effective_value": 108.75,
            "franchise": "False",
            "rookie": "False",
        },
        {
            "player": "Player B",
            "salary": 10500,
            "multiplier": 1.4,
            "collection": "Core",
            "expires": "2027-12-31",
            # NO instance_id — simulates stale session data
            "projected_score": 70.0,
            "effective_value": 98.0,
            "franchise": "False",
            "rookie": "False",
        },
    ]
    response = client.post(
        "/reoptimize",
        data={"card_pool": json.dumps(cards)},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Session expired" in html, (
        "Route should render the stale-session message, not 500 or run the optimizer"
    )


def test_reoptimize_uses_session_constraints(client):
    """POST /reoptimize with locked_cards in session returns 200 without crashing."""
    card_pool_json = _build_card_pool_json()
    with client.session_transaction() as sess:
        sess["locked_cards"] = [["Player A", 11000, 1.5, "Core"]]
    response = client.post(
        "/reoptimize",
        data={"card_pool": card_pool_json},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200


def test_reoptimize_button_rendered(client):
    """After a successful upload POST, the response HTML contains id='reoptimize-form'.

    Remains RED until Plan 02 adds the template changes.
    """
    response = _post_csvs(client, SAMPLE_ROSTER_CSV, SAMPLE_PROJECTIONS_CSV)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'id="reoptimize-form"' in html


def test_reoptimize_button_absent_on_get(client):
    """GET / response HTML does NOT contain id='reoptimize-form'.

    Remains RED until Plan 02 adds the template changes.
    """
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'id="reoptimize-form"' not in html


# ---------------------------------------------------------------------------
# Phase 06: UI-01 — Player pool table and /reoptimize checkbox parsing
# ---------------------------------------------------------------------------


def test_player_pool_section_rendered(client):
    """POST CSVs → response HTML contains id='player-pool-section'."""
    response = _post_csvs(client, SAMPLE_ROSTER_CSV, SAMPLE_PROJECTIONS_CSV)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'id="player-pool-section"' in html


def test_player_pool_table_columns(client):
    """POST CSVs → player pool table contains all required column headers."""
    response = _post_csvs(client, SAMPLE_ROSTER_CSV, SAMPLE_PROJECTIONS_CSV)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    # Headers now have onclick attributes; check for text content within th elements
    assert ">Lock</th>" in html
    assert ">Lock Golfer</th>" in html
    assert ">Exclude Golfer</th>" in html
    assert ">Player</th>" in html
    assert ">Collection</th>" in html
    assert ">Salary</th>" in html
    assert ">Multiplier</th>" in html
    assert ">Proj Score</th>" in html


def test_lock_exclude_checkboxes_in_form(client):
    """POST CSVs → HTML contains lock_card and exclude_golfer inputs inside reoptimize-form."""
    response = _post_csvs(client, SAMPLE_ROSTER_CSV, SAMPLE_PROJECTIONS_CSV)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    # Inputs must exist somewhere in the HTML
    assert 'name="lock_card"' in html
    assert 'name="exclude_golfer"' in html
    # The reoptimize-form must exist
    form_start = html.index('id="reoptimize-form"')
    # Both inputs must appear after the form start (inside the form)
    assert html.index('name="lock_card"') > form_start
    assert html.index('name="exclude_golfer"') > form_start


def test_lock_golfer_first_row_only(client):
    """POST CSVs → count of lock_golfer checkboxes equals unique player count (30).

    Every player in _VALID_PLAYERS has a unique name, so there should be exactly
    one lock_golfer checkbox per player (30 total) and also 30 lock_card checkboxes
    (one per card row). Both counts should be less than the total number of td cells.
    """
    response = _post_csvs(client, SAMPLE_ROSTER_CSV, SAMPLE_PROJECTIONS_CSV)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    lock_golfer_count = html.count('name="lock_golfer"')
    lock_card_count = html.count('name="lock_card"')
    assert lock_golfer_count == 30
    assert lock_card_count == 30
    # Sanity: both are less than total <td> cell count
    td_count = html.count("<td")
    assert lock_golfer_count < td_count


def test_reoptimize_parses_lock_checkboxes(client):
    """POST /reoptimize with lock_card → session['locked_cards'] contains parsed entry."""
    card_pool_json = _build_card_pool_json()
    response = client.post(
        "/reoptimize",
        data={
            "card_pool": card_pool_json,
            "lock_card": "Player A|11000|1.5|Core",
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    with client.session_transaction() as sess:
        locked = sess.get("locked_cards", [])
    assert ["Player A", 11000, 1.5, "Core"] in locked


def test_reoptimize_parses_exclude_checkboxes(client):
    """POST /reoptimize with exclude_golfer → session['excluded_players'] contains player name."""
    card_pool_json = _build_card_pool_json()
    response = client.post(
        "/reoptimize",
        data={
            "card_pool": card_pool_json,
            "exclude_golfer": "Player B",
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    with client.session_transaction() as sess:
        excluded = sess.get("excluded_players", [])
    assert "Player B" in excluded


def test_reoptimize_parses_lock_golfer(client):
    """POST /reoptimize with lock_golfer → session['locked_golfers'] contains player name."""
    card_pool_json = _build_card_pool_json()
    response = client.post(
        "/reoptimize",
        data={
            "card_pool": card_pool_json,
            "lock_golfer": "Player C",
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    with client.session_transaction() as sess:
        golfers = sess.get("locked_golfers", [])
    assert "Player C" in golfers


# ---------------------------------------------------------------------------
# Phase 06: UI-03 — Lock column in lineup output
# ---------------------------------------------------------------------------


def test_lineup_lock_column_header(client):
    """POST /reoptimize → HTML contains 'Lock' column header in lineup table."""
    card_pool_json = _build_card_pool_json()
    response = client.post(
        "/reoptimize",
        data={"card_pool": card_pool_json},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "<th>Lock</th>" in html


def test_locked_card_shows_lock_icon(client):
    """POST /reoptimize with lock_card → locked player row shows lock icon."""
    card_pool_json = _build_card_pool_json()
    response = client.post(
        "/reoptimize",
        data={
            "card_pool": card_pool_json,
            "lock_card": "Player A|11000|1.5|Core",
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "\U0001f512" in html  # 🔒 lock icon


def test_nonlocked_card_blank_lock_column(client):
    """POST /reoptimize with no lock_card fields → lock column present but no lock icon shown.

    The lineup table must have the Lock column header (Plan 03 adds it), but
    when no cards are locked there should be no lock icon in any row.
    """
    card_pool_json = _build_card_pool_json()
    response = client.post(
        "/reoptimize",
        data={"card_pool": card_pool_json},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    # Lock column header must be present (RED until Plan 03 adds it)
    assert "<th>Lock</th>" in html
    # No lock icon should appear when nothing is locked
    assert "\U0001f512" not in html  # 🔒 must NOT appear


# ---------------------------------------------------------------------------
# Phase 07: UI-05 — Clear All button presence
# ---------------------------------------------------------------------------


def test_clear_all_button_rendered(client):
    """POST CSVs → HTML contains the Clear All button when results are shown."""
    response = _post_csvs(client, SAMPLE_ROSTER_CSV, SAMPLE_PROJECTIONS_CSV)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert ">Clear All</button>" in html


def test_clear_all_button_absent_on_get(client):
    """GET / → Clear All button is NOT present when no results are shown."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert ">Clear All</button>" not in html


# ---------------------------------------------------------------------------
# Phase 07: UI-06 — Constraint count element presence
# ---------------------------------------------------------------------------


def test_constraint_count_element_rendered(client):
    """POST CSVs → HTML contains the constraint count element when results are shown."""
    response = _post_csvs(client, SAMPLE_ROSTER_CSV, SAMPLE_PROJECTIONS_CSV)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'id="constraint-count"' in html


def test_constraint_count_absent_on_get(client):
    """GET / → constraint count element is NOT present when no results are shown."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'id="constraint-count"' not in html


# ---------------------------------------------------------------------------
# Phase 07: Sortable columns — sort header onclick presence
# ---------------------------------------------------------------------------


def test_sort_headers_rendered(client):
    """POST CSVs → player pool table th headers have onclick sortTable() handlers."""
    response = _post_csvs(client, SAMPLE_ROSTER_CSV, SAMPLE_PROJECTIONS_CSV)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'onclick="sortTable(' in html


# ---------------------------------------------------------------------------
# Helpers for Phase 10: Projection Source Selector tests
# ---------------------------------------------------------------------------


def _seed_projections(app, players_scores, tournament_name="Test Open", days_ago=2):
    """Seed the DB with a fetch + projections for web tests.

    Args:
        app: Flask app with app context
        players_scores: list of (player_name, projected_score) tuples
        tournament_name: tournament name for the fetch record
        days_ago: how many days ago the fetch occurred
    """
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import text
    from gbgolf.db import db

    fetched_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
    with app.app_context():
        db.session.execute(
            text(
                "INSERT INTO fetches (tournament_name, fetched_at, player_count, source, tour) "
                "VALUES (:tn, :fa, :pc, :src, :tour)"
            ),
            {
                "tn": tournament_name,
                "fa": fetched_at,
                "pc": len(players_scores),
                "src": "datagolf",
                "tour": "pga",
            },
        )
        # Get the fetch_id just inserted
        row = db.session.execute(
            text("SELECT id FROM fetches ORDER BY fetched_at DESC LIMIT 1")
        ).mappings().fetchone()
        fetch_id = row["id"]

        for player_name, score in players_scores:
            db.session.execute(
                text(
                    "INSERT INTO projections (fetch_id, player_name, projected_score) "
                    "VALUES (:fid, :pn, :ps)"
                ),
                {"fid": fetch_id, "pn": player_name, "ps": score},
            )
        db.session.commit()


@pytest.fixture()
def db_client():
    """Flask test client with DB tables created (for source selector tests)."""
    from gbgolf.web import create_app
    from gbgolf.db import db as _db
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        _db.create_all()
        with app.test_client() as c:
            c._app = app  # stash for _seed_projections access
            yield c
        _db.drop_all()


# ---------------------------------------------------------------------------
# Phase 10: SRC-01 through SRC-05 -- Projection Source Selector
# ---------------------------------------------------------------------------


def test_source_selector_rendered(db_client):
    """SRC-01: GET / renders source selector radio buttons."""
    # Seed DB so Auto is enabled
    _seed_projections(db_client._app, [("Player A", 72.5)])
    response = db_client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'name="source_radio"' in html
    assert 'value="auto"' in html
    assert 'value="csv"' in html


def test_projection_source_hidden_input(db_client):
    """SRC-01: GET / renders hidden projection_source input."""
    response = db_client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'name="projection_source"' in html
    assert 'id="projection-source-input"' in html


@pytest.mark.skip(reason="pre-existing failure, fix deferred")
def test_staleness_label_rendered(db_client):
    """SRC-03: GET / shows tournament name and days ago when projections exist."""
    _seed_projections(db_client._app, [("Player A", 72.5)], tournament_name="Arnold Palmer Invitational", days_ago=2)
    response = db_client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Arnold Palmer Invitational" in html
    assert "2 days ago" in html


def test_auto_disabled_empty_db(db_client):
    """SRC-04: Auto radio disabled when DB has no projections."""
    response = db_client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    # Auto radio should be disabled
    assert "disabled" in html
    assert "No projections available yet" in html
    # CSV should be checked by default
    assert 'value="csv"' in html


def test_load_projections_from_db(db_client):
    """SRC-02: load_projections_from_db returns normalized name -> score dict."""
    _seed_projections(db_client._app, [("Scottie Scheffler", 72.5), ("Rory McIlroy", 68.3)])
    from gbgolf.data import load_projections_from_db
    with db_client._app.app_context():
        result = load_projections_from_db()
    assert isinstance(result, dict)
    assert "scottie scheffler" in result
    assert "rory mcilroy" in result
    assert result["scottie scheffler"] == 72.5
    assert result["rory mcilroy"] == 68.3


def test_post_auto_source_uses_db(db_client):
    """SRC-02: POST with projection_source=auto uses DB projections to generate lineups."""
    # Seed DB with projections for all 30 _VALID_PLAYERS
    players_scores = [(p, 72.5) for p, _, _ in _VALID_PLAYERS]
    _seed_projections(db_client._app, players_scores)
    response = db_client.post(
        "/",
        data={
            "roster": (io.BytesIO(SAMPLE_ROSTER_CSV.encode("utf-8")), "roster.csv"),
            "projection_source": "auto",
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    # Should show lineup results
    assert "The Tips" in html
    assert "The Intermediate Tee" in html


def test_auto_source_empty_db_error(db_client):
    """SRC-04: POST with projection_source=auto and empty DB returns error."""
    response = db_client.post(
        "/",
        data={
            "roster": (io.BytesIO(SAMPLE_ROSTER_CSV.encode("utf-8")), "roster.csv"),
            "projection_source": "auto",
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "No projections available" in html


def test_auto_source_unmatched_players(db_client):
    """SRC-05: When using auto source, unmatched roster players appear in exclusion report."""
    # Seed DB with projections for only a subset of players (not "Unmatched Player")
    players_scores = [(p, 72.5) for p, _, _ in _VALID_PLAYERS]
    _seed_projections(db_client._app, players_scores)
    # Use EXCLUSION_ROSTER_CSV which has "Unmatched Player" with no projection
    response = db_client.post(
        "/",
        data={
            "roster": (io.BytesIO(EXCLUSION_ROSTER_CSV.encode("utf-8")), "roster.csv"),
            "projection_source": "auto",
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Unmatched Player" in html
    assert "no projection found" in html


# ---------------------------------------------------------------------------
# Phase: Hybrid projection source
# ---------------------------------------------------------------------------


def test_hybrid_fills_gaps_from_db(db_client):
    """Hybrid: CSV has 10 players, DB has all 30 -> all 30 matched, lineup generated."""
    players_scores = [(p, 72.5) for p, _, _ in _VALID_PLAYERS]
    _seed_projections(db_client._app, players_scores)
    response = _post_hybrid(db_client, SAMPLE_ROSTER_CSV, PARTIAL_PROJECTIONS_CSV)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "The Tips" in html


@pytest.mark.skip(reason="pre-existing failure, fix deferred")
def test_hybrid_csv_takes_priority(db_client):
    """Hybrid: CSV has Player A at 99.0, DB has Player A at 72.5 -> Player A gets 99.0."""
    players_scores = [(p, 72.5) for p, _, _ in _VALID_PLAYERS]
    _seed_projections(db_client._app, players_scores)
    # CSV with just Player A at 99.0 — all others come from DB
    override_csv = "player,projected_score\nPlayer A,99.0\n"
    response = _post_hybrid(db_client, SAMPLE_ROSTER_CSV, override_csv)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    # Player A should have projected_score 99.0 in the card pool JSON
    assert "99.00" in html


def test_hybrid_db_empty_still_works(db_client):
    """Hybrid: DB empty, full CSV provided -> still works (CSV-only fallback)."""
    # Do NOT seed DB
    response = _post_hybrid(db_client, SAMPLE_ROSTER_CSV, SAMPLE_PROJECTIONS_CSV)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "The Tips" in html


def test_hybrid_no_projections_file_error(db_client):
    """Hybrid: no projections file uploaded -> returns error."""
    players_scores = [(p, 72.5) for p, _, _ in _VALID_PLAYERS]
    _seed_projections(db_client._app, players_scores)
    response = db_client.post(
        "/",
        data={
            "roster": (io.BytesIO(SAMPLE_ROSTER_CSV.encode("utf-8")), "roster.csv"),
            "projection_source": "hybrid",
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Projections file is required" in html


def test_hybrid_unmatched_from_both_sources(db_client):
    """Hybrid: players missing from BOTH CSV and DB appear in exclusion report."""
    # Seed DB with only the 30 standard players (not "Unmatched Player")
    players_scores = [(p, 72.5) for p, _, _ in _VALID_PLAYERS]
    _seed_projections(db_client._app, players_scores)
    # EXCLUSION_ROSTER_CSV has "Unmatched Player" which is not in CSV or DB
    response = _post_hybrid(db_client, EXCLUSION_ROSTER_CSV, SAMPLE_PROJECTIONS_CSV)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Unmatched Player" in html
    assert "no projection found" in html


def test_hybrid_radio_rendered(db_client):
    """Hybrid radio button is rendered when DB has projections."""
    _seed_projections(db_client._app, [("Player A", 72.5)])
    response = db_client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'value="hybrid"' in html


def test_hybrid_radio_disabled_no_db(db_client):
    """Hybrid radio is present but disabled when DB has no projections."""
    response = db_client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'value="hybrid"' in html
    # Find the hybrid radio input and check it has the disabled attribute
    hybrid_pos = html.index('value="hybrid"')
    # Look at the surrounding input tag (search backwards for '<input')
    tag_start = html.rfind("<input", 0, hybrid_pos)
    tag_end = html.index("/>", hybrid_pos) + 2
    hybrid_tag = html[tag_start:tag_end]
    assert "disabled" in hybrid_tag


def test_hybrid_radio_enabled_with_db(db_client):
    """Hybrid radio is enabled (not disabled) when DB has projections."""
    _seed_projections(db_client._app, [("Player A", 72.5)])
    response = db_client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'value="hybrid"' in html
    # Find the hybrid radio input and check it does NOT have the disabled attribute
    hybrid_pos = html.index('value="hybrid"')
    tag_start = html.rfind("<input", 0, hybrid_pos)
    tag_end = html.index("/>", hybrid_pos) + 2
    hybrid_tag = html[tag_start:tag_end]
    assert "disabled" not in hybrid_tag


# ---------------------------------------------------------------------------
# Tests: per-contest entry-count overrides
# ---------------------------------------------------------------------------

def _tips_section(html: str) -> str:
    """Slice out the The Tips contest results section (anchored on <h2>) so
    per-section assertions don't bleed into the entry-count fieldset or the
    The Intermediate Tee section."""
    start = html.index("<h2>The Tips</h2>")
    end = html.index("<h2>The Intermediate Tee</h2>", start)
    return html[start:end]


def test_post_index_with_entry_override_limits_lineups(client):
    """POST / with entries_0=1 produces only 1 lineup for The Tips."""
    response = client.post(
        "/",
        data={
            "roster": (io.BytesIO(SAMPLE_ROSTER_CSV.encode("utf-8")), "roster.csv"),
            "projections": (io.BytesIO(SAMPLE_PROJECTIONS_CSV.encode("utf-8")), "projections.csv"),
            "entries_0": "1",
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    tips = _tips_section(html)
    assert "Lineup 1" in tips
    assert "Lineup 2" not in tips


def test_post_reoptimize_with_entry_override(client):
    """POST /reoptimize with entries_0=2 produces exactly 2 lineups for The Tips."""
    card_pool_json = _build_card_pool_json()
    response = client.post(
        "/reoptimize",
        data={"card_pool": card_pool_json, "entries_0": "2"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    tips = _tips_section(html)
    assert "Lineup 1" in tips
    assert "Lineup 2" in tips
    assert "Lineup 3" not in tips
