"""
DataGolf projection fetcher for GB Golf Optimizer.

Fetches player projections from the DataGolf fantasy-projection-defaults API,
normalizes player names, and writes them to the fetches + projections tables.

Cron schedule for Phase 11 VPS deployment:
    # Tuesday and Wednesday at 8:00 AM Eastern Time
    # Winter (EST = UTC-5): 0 13 * * 2,3
    # Summer (EDT = UTC-4): 0 12 * * 2,3
    # Verify VPS timezone with `timedatectl` before setting.
    # Example crontab entry (winter):
    #   0 13 * * 2,3 cd /var/www/gbgolf && FLASK_APP=gbgolf.web:create_app .venv/bin/flask fetch-projections
    # The .env file must be in the project root with DATAGOLF_API_KEY set.
"""
import os
from datetime import datetime, UTC

import httpx
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text

from gbgolf.data.matching import normalize_name  # noqa: F401 — available for future use
from gbgolf.db import db


# ---------------------------------------------------------------------------
# Pydantic boundary model (field names from live API discovery)
# ---------------------------------------------------------------------------

class _DataGolfPlayerProjection(BaseModel):
    """Validate one player record from the DataGolf API response.

    Field names confirmed from live discovery call (2026-03-25):
    - player_name: "Last, First" format (e.g. "Scheffler, Scottie")
    - proj_points_total: total projected DraftKings fantasy points
    """

    player_name: str
    proj_points_total: float

    model_config = ConfigDict(extra="ignore")


# ---------------------------------------------------------------------------
# Name parsing (FETCH-06)
# ---------------------------------------------------------------------------

def parse_datagolf_name(raw: str) -> str:
    """Convert DataGolf 'Last, First' format to 'First Last'.

    Handles:
    - "Scheffler, Scottie" -> "Scottie Scheffler"
    - "Thomas Jr., Justin" -> "Justin Thomas Jr."
    - "Tiger Woods" (no comma) -> "Tiger Woods" (passthrough)
    - Extra whitespace stripped
    """
    if "," in raw:
        parts = raw.split(",", 1)
        return f"{parts[1].strip()} {parts[0].strip()}"
    return raw.strip()


# ---------------------------------------------------------------------------
# Fetch logging (FETCH-03)
# ---------------------------------------------------------------------------

def write_fetch_log(log_dir: str, line: str) -> None:
    """Append one timestamped line to {log_dir}/fetch.log.

    Creates the directory if it does not exist.
    Format: "YYYY-MM-DD HH:MM:SS UTC | {line}"
    """
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "fetch.log")
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {line}\n")


# ---------------------------------------------------------------------------
# Database writes (atomic upsert)
# ---------------------------------------------------------------------------

def write_projections(session, tournament_name: str, tour: str, players: list[dict]) -> int:
    """Atomic upsert: delete stale data for this tournament, insert fresh batch.

    Uses DELETE CASCADE on fetches to remove old projections, then INSERTs
    a new fetches row + all projection rows in one transaction.

    Returns the new fetch_id.
    """
    # Enable FK constraints for SQLite (no-op on PostgreSQL)
    session.execute(text("PRAGMA foreign_keys = ON"))

    # DELETE old data for this tournament/tour (CASCADE deletes projections)
    session.execute(
        text("DELETE FROM fetches WHERE tournament_name = :tn AND tour = :tour"),
        {"tn": tournament_name, "tour": tour},
    )

    # INSERT new fetch row
    result = session.execute(
        text(
            "INSERT INTO fetches (tournament_name, fetched_at, player_count, source, tour) "
            "VALUES (:tn, :fa, :pc, :src, :tour) RETURNING id"
        ),
        {
            "tn": tournament_name,
            "fa": datetime.now(UTC),
            "pc": len(players),
            "src": "datagolf",
            "tour": tour,
        },
    )
    fetch_id = result.scalar_one()

    # INSERT projection rows
    for p in players:
        session.execute(
            text(
                "INSERT INTO projections (fetch_id, player_name, projected_score) "
                "VALUES (:fid, :pn, :ps)"
            ),
            {
                "fid": fetch_id,
                "pn": p["player_name"],
                "ps": p["projected_score"],
            },
        )

    session.commit()
    return fetch_id


# ---------------------------------------------------------------------------
# Fetch orchestration (FETCH-01, FETCH-04)
# ---------------------------------------------------------------------------

def run_fetch(log_dir: str = "logs") -> str:
    """Fetch player projections from DataGolf and write to database.

    1. Call DataGolf fantasy-projection-defaults API
    2. Validate response (>= 30 players)
    3. Parse through Pydantic model, normalize names
    4. Atomic DB write (DELETE CASCADE + INSERT)
    5. Log activity to fetch.log

    Returns a summary string (for CLI output).
    """
    api_key = os.environ.get("DATAGOLF_API_KEY", "")

    # --- HTTP call with error handling ---
    try:
        response = httpx.get(
            "https://feeds.datagolf.com/preds/fantasy-projection-defaults",
            params={
                "tour": "pga",
                "site": "draftkings",
                "slate": "main",
                "file_format": "json",
                "key": api_key,
            },
            timeout=30.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        error_msg = f"API returned HTTP {exc.response.status_code}"
        write_fetch_log(log_dir, f"ERROR | {error_msg} | existing data preserved")
        return f"ERROR: {error_msg}"
    except httpx.ConnectError as exc:
        error_msg = f"Connection error: {exc}"
        write_fetch_log(log_dir, f"ERROR | {error_msg} | existing data preserved")
        return f"ERROR: {error_msg}"
    except httpx.TimeoutException:
        error_msg = "Request timed out"
        write_fetch_log(log_dir, f"ERROR | {error_msg} | existing data preserved")
        return f"ERROR: {error_msg}"
    except Exception as exc:
        error_msg = f"Unexpected error: {type(exc).__name__}: {exc}"
        write_fetch_log(log_dir, f"ERROR | {error_msg} | existing data preserved")
        return f"ERROR: {error_msg}"

    # --- Parse response ---
    data = response.json()
    raw_players = data.get("projections", [])
    tournament_name = data.get("event_name", "Unknown Event")

    # Validate through Pydantic boundary model
    players = [_DataGolfPlayerProjection.model_validate(item) for item in raw_players]

    # --- Guard: minimum player count (FETCH-04) ---
    if len(players) < 30:
        error_msg = f"Only {len(players)} players returned (minimum 30)"
        write_fetch_log(log_dir, f"ERROR | {error_msg} | existing data preserved")
        return f"ERROR: {error_msg}"

    # --- Normalize names and build DB-ready list ---
    players_list = []
    for player in players:
        display_name = parse_datagolf_name(player.player_name)
        players_list.append({
            "player_name": display_name,
            "projected_score": player.proj_points_total,
        })

    # --- Atomic DB write ---
    fetch_id = write_projections(db.session, tournament_name, "pga", players_list)

    # --- Log success ---
    write_fetch_log(
        log_dir,
        f"OK | {tournament_name} | {len(players_list)} players | fetch_id={fetch_id}",
    )

    return f"OK: {tournament_name} | {len(players_list)} players | fetch_id={fetch_id}"
