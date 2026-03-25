"""Tests for DataGolf fetcher module (FETCH-01, FETCH-03, FETCH-04, FETCH-06)."""
import os
from datetime import datetime, UTC

import httpx
import pytest
from sqlalchemy import text

from gbgolf.fetcher import parse_datagolf_name, write_fetch_log, write_projections, run_fetch


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

class MockResponse:
    """Mimics httpx.Response for monkeypatched httpx.get."""

    def __init__(self, json_data, status_code=200):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error", request=httpx.Request("GET", "http://test"), response=self,
            )


def _make_player(name="Scheffler, Scottie", pts=72.5):
    """Build a single player dict matching DataGolf response shape."""
    return {
        "dg_id": 1,
        "player_name": name,
        "proj_points_total": pts,
        "salary": 10000,
        "proj_ownership": 20.0,
        "proj_points_finish": 5.0,
        "proj_points_scoring": pts - 5.0,
        "early_late_wave": 0,
        "r1_teetime": "8:00 am",
        "site_name_id": "test",
        "std_dev": 30.0,
        "value": 1.0,
    }


def _make_api_response(player_count=50, event_name="Test Open"):
    """Build a full API response dict."""
    players = [_make_player(f"Player{i}, First{i}", 60.0 + i) for i in range(player_count)]
    return {
        "event_name": event_name,
        "last_updated": "2026-03-25 12:00:00 UTC",
        "note": "projections released",
        "projections": players,
        "site": "draftkings",
        "slate": "main",
        "tour": "pga",
    }


# ---------------------------------------------------------------------------
# parse_datagolf_name tests (FETCH-06)
# ---------------------------------------------------------------------------

def test_parse_datagolf_name():
    """Standard 'Last, First' format."""
    assert parse_datagolf_name("Scheffler, Scottie") == "Scottie Scheffler"


def test_parse_datagolf_name_suffix():
    """Suffix stays with last name part: 'Last Jr., First' -> 'First Last Jr.'"""
    assert parse_datagolf_name("Horschel, Billy") == "Billy Horschel"
    assert parse_datagolf_name("Thomas Jr., Justin") == "Justin Thomas Jr."


def test_parse_datagolf_name_no_comma():
    """No comma = passthrough."""
    assert parse_datagolf_name("Tiger Woods") == "Tiger Woods"


def test_parse_datagolf_name_whitespace():
    """Extra whitespace is stripped."""
    assert parse_datagolf_name(" Scheffler , Scottie ") == "Scottie Scheffler"


# ---------------------------------------------------------------------------
# write_fetch_log tests (FETCH-03)
# ---------------------------------------------------------------------------

def test_write_fetch_log_ok(tmp_path):
    """OK log line follows the specified format."""
    log_dir = str(tmp_path / "logs")
    write_fetch_log(log_dir, "OK | Test Open | 50 players | fetch_id=1")
    log_path = os.path.join(log_dir, "fetch.log")
    assert os.path.exists(log_path)
    content = open(log_path).read()
    assert "UTC | OK | Test Open | 50 players | fetch_id=1" in content


def test_write_fetch_log_error(tmp_path):
    """ERROR log line follows the specified format."""
    log_dir = str(tmp_path / "logs")
    write_fetch_log(log_dir, "ERROR | API returned 403 | existing data preserved")
    content = open(os.path.join(log_dir, "fetch.log")).read()
    assert "UTC | ERROR | API returned 403 | existing data preserved" in content


def test_write_fetch_log_creates_dir(tmp_path):
    """logs/ directory created if it does not exist."""
    log_dir = str(tmp_path / "nonexistent" / "logs")
    assert not os.path.exists(log_dir)
    write_fetch_log(log_dir, "OK | test")
    assert os.path.exists(log_dir)
    assert os.path.exists(os.path.join(log_dir, "fetch.log"))


# ---------------------------------------------------------------------------
# write_projections tests (DB writes)
# ---------------------------------------------------------------------------

def test_write_projections_inserts(db_session):
    """Inserts a fetches row + projection rows, returns fetch_id > 0."""
    db_session.execute(text("PRAGMA foreign_keys = ON"))
    players = [
        {"player_name": "Scottie Scheffler", "projected_score": 72.5},
        {"player_name": "Rory McIlroy", "projected_score": 68.3},
    ]
    fetch_id = write_projections(db_session, "Test Open", "pga", players)
    assert fetch_id > 0

    row = db_session.execute(
        text("SELECT * FROM fetches WHERE id = :fid"), {"fid": fetch_id}
    ).mappings().one()
    assert row["tournament_name"] == "Test Open"
    assert row["player_count"] == 2
    assert row["tour"] == "pga"

    proj_count = db_session.execute(
        text("SELECT COUNT(*) FROM projections WHERE fetch_id = :fid"),
        {"fid": fetch_id},
    ).scalar_one()
    assert proj_count == 2


def test_write_projections_replaces_stale(db_session):
    """Second call for same tournament deletes old rows via CASCADE, inserts new."""
    db_session.execute(text("PRAGMA foreign_keys = ON"))
    old_players = [{"player_name": "Old Player", "projected_score": 60.0}]
    write_projections(db_session, "Test Open", "pga", old_players)

    # Verify old data exists
    old_proj_name = db_session.execute(
        text("SELECT player_name FROM projections")
    ).scalar_one()
    assert old_proj_name == "Old Player"

    new_players = [
        {"player_name": "New Player A", "projected_score": 70.0},
        {"player_name": "New Player B", "projected_score": 71.0},
    ]
    write_projections(db_session, "Test Open", "pga", new_players)

    # Only one fetch row should exist (old one replaced)
    fetch_count = db_session.execute(
        text("SELECT COUNT(*) FROM fetches WHERE tournament_name = 'Test Open'")
    ).scalar_one()
    assert fetch_count == 1

    # Old projection ("Old Player") should be gone, replaced by new data
    names = [
        r["player_name"]
        for r in db_session.execute(text("SELECT player_name FROM projections")).mappings().all()
    ]
    assert "Old Player" not in names
    assert "New Player A" in names
    assert "New Player B" in names
    assert len(names) == 2


def test_write_projections_idempotent(db_session):
    """Calling twice with same data leaves exactly one fetch + N projections."""
    db_session.execute(text("PRAGMA foreign_keys = ON"))
    players = [
        {"player_name": "Player A", "projected_score": 65.0},
        {"player_name": "Player B", "projected_score": 66.0},
    ]
    write_projections(db_session, "Idempotent Open", "pga", players)
    write_projections(db_session, "Idempotent Open", "pga", players)

    fetch_count = db_session.execute(
        text("SELECT COUNT(*) FROM fetches WHERE tournament_name = 'Idempotent Open'")
    ).scalar_one()
    assert fetch_count == 1

    proj_count = db_session.execute(
        text("SELECT COUNT(*) FROM projections")
    ).scalar_one()
    assert proj_count == 2


# ---------------------------------------------------------------------------
# run_fetch tests (integration, mocked httpx)
# ---------------------------------------------------------------------------

def test_run_fetch_success(app, db_session, monkeypatch, tmp_path):
    """Mocked httpx returns valid response with 50+ players, DB has rows after call."""
    log_dir = str(tmp_path / "logs")
    api_response = _make_api_response(player_count=50, event_name="Success Open")

    monkeypatch.setattr(httpx, "get", lambda *a, **kw: MockResponse(api_response))
    monkeypatch.setenv("DATAGOLF_API_KEY", "test-key")

    result = run_fetch(log_dir=log_dir)

    assert "Success Open" in result
    assert "50" in result

    fetch_count = db_session.execute(
        text("SELECT COUNT(*) FROM fetches WHERE tournament_name = 'Success Open'")
    ).scalar_one()
    assert fetch_count == 1

    proj_count = db_session.execute(
        text("SELECT COUNT(*) FROM projections")
    ).scalar_one()
    assert proj_count == 50

    log_content = open(os.path.join(log_dir, "fetch.log")).read()
    assert "OK" in log_content
    assert "Success Open" in log_content


def test_run_fetch_low_count_guard(app, db_session, monkeypatch, tmp_path):
    """< 30 players: DB unchanged, log has ERROR line."""
    log_dir = str(tmp_path / "logs")

    # Pre-seed some data to verify it is preserved
    db_session.execute(text("PRAGMA foreign_keys = ON"))
    db_session.execute(text("""
        INSERT INTO fetches (tournament_name, fetched_at, player_count, source, tour)
        VALUES ('Existing Open', :fa, 80, 'datagolf', 'pga')
    """), {"fa": datetime.now(UTC)})
    db_session.commit()
    existing_count = db_session.execute(
        text("SELECT COUNT(*) FROM fetches")
    ).scalar_one()
    assert existing_count == 1

    api_response = _make_api_response(player_count=10, event_name="Small Field Open")
    monkeypatch.setattr(httpx, "get", lambda *a, **kw: MockResponse(api_response))
    monkeypatch.setenv("DATAGOLF_API_KEY", "test-key")

    result = run_fetch(log_dir=log_dir)

    assert "ERROR" in result or "error" in result.lower()

    # Existing data preserved
    preserved = db_session.execute(
        text("SELECT COUNT(*) FROM fetches")
    ).scalar_one()
    assert preserved == 1

    log_content = open(os.path.join(log_dir, "fetch.log")).read()
    assert "ERROR" in log_content
    assert "existing data preserved" in log_content


def test_run_fetch_api_error(app, db_session, monkeypatch, tmp_path):
    """HTTPStatusError: DB unchanged, log has ERROR line."""
    log_dir = str(tmp_path / "logs")

    monkeypatch.setattr(
        httpx, "get",
        lambda *a, **kw: MockResponse({"error": "forbidden"}, status_code=403),
    )
    monkeypatch.setenv("DATAGOLF_API_KEY", "test-key")

    result = run_fetch(log_dir=log_dir)

    assert "ERROR" in result or "error" in result.lower()

    fetch_count = db_session.execute(
        text("SELECT COUNT(*) FROM fetches")
    ).scalar_one()
    assert fetch_count == 0

    log_content = open(os.path.join(log_dir, "fetch.log")).read()
    assert "ERROR" in log_content


def test_run_fetch_network_error(app, db_session, monkeypatch, tmp_path):
    """ConnectError: DB unchanged, log has ERROR line."""
    log_dir = str(tmp_path / "logs")

    def raise_connect_error(*a, **kw):
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(httpx, "get", raise_connect_error)
    monkeypatch.setenv("DATAGOLF_API_KEY", "test-key")

    result = run_fetch(log_dir=log_dir)

    assert "ERROR" in result or "error" in result.lower()

    fetch_count = db_session.execute(
        text("SELECT COUNT(*) FROM fetches")
    ).scalar_one()
    assert fetch_count == 0

    log_content = open(os.path.join(log_dir, "fetch.log")).read()
    assert "ERROR" in log_content


def test_run_fetch_normalizes_names(app, db_session, monkeypatch, tmp_path):
    """Mocked response has 'Scheffler, Scottie', DB stores 'Scottie Scheffler'."""
    log_dir = str(tmp_path / "logs")

    # Build 50 players, put Scheffler as first
    players = [_make_player("Scheffler, Scottie", 72.5)]
    players += [_make_player(f"Player{i}, First{i}", 60.0 + i) for i in range(49)]
    api_response = {
        "event_name": "Name Test Open",
        "last_updated": "2026-03-25 12:00:00 UTC",
        "note": "projections released",
        "projections": players,
        "site": "draftkings",
        "slate": "main",
        "tour": "pga",
    }

    monkeypatch.setattr(httpx, "get", lambda *a, **kw: MockResponse(api_response))
    monkeypatch.setenv("DATAGOLF_API_KEY", "test-key")

    run_fetch(log_dir=log_dir)

    row = db_session.execute(
        text("SELECT player_name FROM projections WHERE player_name = 'Scottie Scheffler'")
    ).mappings().fetchone()
    assert row is not None
    assert row["player_name"] == "Scottie Scheffler"


# ---------------------------------------------------------------------------
# CLI command tests (FETCH-02)
# ---------------------------------------------------------------------------

def test_cli_command_registered(app):
    """FETCH-02: flask fetch-projections CLI command exists."""
    runner = app.test_cli_runner()
    # --help should work without making an API call
    result = runner.invoke(args=["fetch-projections", "--help"])
    assert result.exit_code == 0
    assert "Fetch player projections" in result.output


def test_cli_command_invokes_run_fetch(app, monkeypatch):
    """FETCH-01/02: CLI command calls run_fetch and echoes result."""
    called = {}

    def mock_run_fetch(log_dir="logs"):
        called["invoked"] = True
        return "OK | Test Tournament | 50 players | fetch_id=1"

    monkeypatch.setattr("gbgolf.fetcher.run_fetch", mock_run_fetch)
    runner = app.test_cli_runner()
    result = runner.invoke(args=["fetch-projections"])
    assert result.exit_code == 0
    assert called.get("invoked") is True
    assert "OK | Test Tournament" in result.output
