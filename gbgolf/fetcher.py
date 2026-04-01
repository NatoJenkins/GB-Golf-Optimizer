"""
DataGolf projection fetcher for GB Golf Optimizer.

Fetches player projections from the DataGolf fantasy-projection-defaults API,
normalizes player names, and writes them to the fetches + projections tables.

Cron schedule (VPS runs UTC, EDT = UTC-4):
    Every 2 hours, 10am–10pm EDT, Tuesday and Wednesday only.
    0 14,16,18,20,22 * * 2,3  (10am–6pm EDT, same UTC day)
    0 0 * * 3,4               (8pm EDT, midnight UTC next day)
    0 2 * * 3,4               (10pm EDT, 2am UTC next day)
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

def parse_datagolf_updated_at(raw: str | None) -> "datetime | None":
    """Parse DataGolf 'last_updated' string to an aware UTC datetime.

    Accepts formats like "2026-03-25 12:00:00 UTC" or ISO 8601.
    Returns None if raw is absent or unparseable.
    """
    if not raw:
        return None
    try:
        # Handle "YYYY-MM-DD HH:MM:SS UTC"
        cleaned = raw.replace(" UTC", "+00:00").replace(" ", "T", 1)
        return datetime.fromisoformat(cleaned)
    except (ValueError, TypeError):
        return None


def write_projections(session, tournament_name: str, tour: str, players: list[dict], datagolf_updated_at=None) -> int:
    """Atomic upsert: delete stale data for this tournament, insert fresh batch.

    Uses DELETE CASCADE on fetches to remove old projections, then INSERTs
    a new fetches row + all projection rows in one transaction.

    Returns the new fetch_id.
    """
    # Enable FK constraints for SQLite (PostgreSQL always enforces FKs)
    if session.get_bind().dialect.name == "sqlite":
        session.execute(text("PRAGMA foreign_keys = ON"))

    # DELETE old data for this tournament/tour (CASCADE deletes projections)
    session.execute(
        text("DELETE FROM fetches WHERE tournament_name = :tn AND tour = :tour"),
        {"tn": tournament_name, "tour": tour},
    )

    # INSERT new fetch row
    result = session.execute(
        text(
            "INSERT INTO fetches (tournament_name, fetched_at, player_count, source, tour, datagolf_updated_at) "
            "VALUES (:tn, :fa, :pc, :src, :tour, :dg_ua) RETURNING id"
        ),
        {
            "tn": tournament_name,
            "fa": datetime.now(UTC),
            "pc": len(players),
            "src": "datagolf",
            "tour": tour,
            "dg_ua": datagolf_updated_at,
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
    datagolf_updated_at = parse_datagolf_updated_at(data.get("last_updated"))

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
    fetch_id = write_projections(db.session, tournament_name, "pga", players_list, datagolf_updated_at)

    # --- Log success ---
    write_fetch_log(
        log_dir,
        f"OK | {tournament_name} | {len(players_list)} players | fetch_id={fetch_id}",
    )

    return f"OK: {tournament_name} | {len(players_list)} players | fetch_id={fetch_id}"
