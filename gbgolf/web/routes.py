"""
Flask blueprint: index route handling file uploads and lineup generation.
"""
import json
import os
import tempfile
from datetime import date, datetime, timezone

from flask import Blueprint, current_app, render_template, request, session
from sqlalchemy import text

from gbgolf.data import validate_pipeline, validate_pipeline_auto
from gbgolf.data.models import Card
from gbgolf.db import db
from gbgolf.optimizer import optimize
from gbgolf.optimizer.constraints import ConstraintSet, check_conflicts, check_feasibility


def _serialize_cards(cards: list) -> str:
    """Serialize a list of Card objects to JSON for the hidden form field."""
    return json.dumps([
        {
            "player": c.player,
            "salary": c.salary,
            "multiplier": c.multiplier,
            "collection": c.collection,
            "expires": c.expires.isoformat() if c.expires else None,
            "projected_score": c.projected_score,
            "effective_value": c.effective_value,
            "franchise": c.franchise,
            "rookie": c.rookie,
        }
        for c in cards
    ])


def _deserialize_cards(json_str: str) -> list:
    """Reconstruct Card objects from a JSON string. Returns list[Card]."""
    raw = json.loads(json_str)
    cards = []
    for d in raw:
        expires = None
        if d.get("expires"):
            expires = date.fromisoformat(d["expires"])
        cards.append(Card(
            player=d["player"],
            salary=int(d["salary"]),
            multiplier=float(d["multiplier"]),
            collection=d["collection"],
            expires=expires,
            projected_score=d.get("projected_score"),
            effective_value=d.get("effective_value"),
            franchise=d.get("franchise", ""),
            rookie=d.get("rookie", ""),
        ))
    return cards


def _get_latest_fetch():
    """Query latest fetch record for staleness label. Returns dict or None."""
    row = db.session.execute(
        text("SELECT tournament_name, fetched_at FROM fetches ORDER BY fetched_at DESC LIMIT 1")
    ).mappings().fetchone()
    if row is None:
        return None
    fetched_at = row["fetched_at"]
    now = datetime.now(timezone.utc)
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)
    delta = now - fetched_at
    return {
        "tournament_name": row["tournament_name"],
        "days_ago": delta.days,
        "is_stale": delta.days >= 7,
    }


def _db_template_vars():
    """Return dict of DB-related template variables for render_template()."""
    latest_fetch = _get_latest_fetch()
    return {
        "latest_fetch": latest_fetch,
        "db_has_projections": latest_fetch is not None,
    }


bp = Blueprint("main", __name__)


@bp.route("/", methods=["GET", "POST"])
def index():
    """Main page: upload form (GET) and optimization results (POST)."""
    if request.method == "GET":
        return render_template("index.html", **_db_template_vars())

    # --- POST: handle file uploads ---
    roster_file = request.files.get("roster")
    if not roster_file or roster_file.filename == "":
        return render_template("index.html", error="Roster file is required.", **_db_template_vars())

    projection_source = request.form.get("projection_source", "csv")

    # Validate: projections file required only for CSV source
    projections_file = request.files.get("projections")
    if projection_source == "csv" and (not projections_file or projections_file.filename == ""):
        return render_template("index.html", error="Projections file is required.", **_db_template_vars())

    # CLEAR lock/exclude session keys on file upload (UI-04)
    lock_reset = False
    if request.files.get("roster") or request.files.get("projections"):
        session.pop("locked_cards", None)
        session.pop("locked_golfers", None)
        session.pop("excluded_cards", None)
        session.pop("excluded_players", None)
        lock_reset = True

    # BUILD ConstraintSet from session (tuples re-cast from JSON lists after clear)
    constraints = ConstraintSet(
        locked_cards=[tuple(k) for k in session.get("locked_cards", [])],
        locked_golfers=session.get("locked_golfers", []),
        excluded_cards=[tuple(k) for k in session.get("excluded_cards", [])],
        excluded_players=session.get("excluded_players", []),
    )

    roster_tmp = None
    projections_tmp = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="wb") as rf:
            roster_file.save(rf)
            roster_tmp = rf.name

        config_path = current_app.config["CONFIG_PATH"]

        if projection_source == "auto":
            validation = validate_pipeline_auto(roster_tmp, config_path)
        else:
            if not projections_file:
                return render_template("index.html", error="Projections file is required.", **_db_template_vars())
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="wb") as pf:
                projections_file.save(pf)
                projections_tmp = pf.name
            validation = validate_pipeline(roster_tmp, projections_tmp, config_path)

        result = optimize(validation.valid_cards, current_app.config["CONTESTS"], constraints=constraints)

        card_pool_json = _serialize_cards(validation.valid_cards)
        return render_template(
            "index.html",
            validation=validation,
            result=result,
            show_results=True,
            lock_reset=lock_reset,
            card_pool_json=card_pool_json,
            card_pool=sorted(validation.valid_cards, key=lambda c: (c.player, -c.salary)),
            locked_card_keys=set(),
            locked_golfer_set=set(),
            excluded_player_set=set(),
            **_db_template_vars(),
        )

    except ValueError as exc:
        return render_template("index.html", error=str(exc), **_db_template_vars())

    finally:
        if roster_tmp and os.path.exists(roster_tmp):
            try:
                os.unlink(roster_tmp)
            except OSError:
                pass
        if projections_tmp and os.path.exists(projections_tmp):
            try:
                os.unlink(projections_tmp)
            except OSError:
                pass


@bp.route("/reoptimize", methods=["POST"])
def reoptimize():
    """Re-run optimizer using the serialized card pool from the hidden form field."""
    card_pool_json = request.form.get("card_pool")
    if not card_pool_json:
        return render_template(
            "index.html",
            error="Session expired — please re-upload your files",
            **_db_template_vars(),
        )

    try:
        valid_cards = _deserialize_cards(card_pool_json)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return render_template(
            "index.html",
            error="Session expired — please re-upload your files",
            **_db_template_vars(),
        )

    def _parse_card_keys(raw_list):
        """Parse pipe-delimited card key strings into (player, salary, multiplier, collection) tuples."""
        result = []
        for v in raw_list:
            parts = v.split("|")
            if len(parts) != 4:
                continue
            try:
                result.append((parts[0], int(parts[1]), float(parts[2]), parts[3]))
            except (ValueError, TypeError):
                continue
        return result

    # Parse checkbox submissions from form
    locked_cards = _parse_card_keys(request.form.getlist("lock_card"))
    locked_golfers = [v for v in request.form.getlist("lock_golfer") if v]
    excluded_players = [v for v in request.form.getlist("exclude_golfer") if v]

    # Write parsed constraints to session
    session["locked_cards"] = [list(k) for k in locked_cards]
    session["locked_golfers"] = locked_golfers
    session["excluded_players"] = excluded_players

    # Build ConstraintSet from parsed values (not from session re-read)
    constraints = ConstraintSet(
        locked_cards=locked_cards,
        locked_golfers=locked_golfers,
        excluded_players=excluded_players,
    )

    # Pre-solve checks before optimize
    conflict_result = check_conflicts(constraints)
    if conflict_result is not None:
        return render_template(
            "index.html",
            error=conflict_result.message,
            show_results=False,
            card_pool_json=card_pool_json,
            **_db_template_vars(),
        )

    for contest_config in current_app.config["CONTESTS"]:
        feasibility_result = check_feasibility(constraints, valid_cards, contest_config)
        if feasibility_result is not None:
            return render_template(
                "index.html",
                error=feasibility_result.message,
                show_results=False,
                card_pool_json=card_pool_json,
                **_db_template_vars(),
            )

    result = optimize(valid_cards, current_app.config["CONTESTS"], constraints=constraints)

    return render_template(
        "index.html",
        result=result,
        show_results=True,
        lock_reset=False,
        card_pool_json=card_pool_json,
        card_pool=sorted(valid_cards, key=lambda c: (c.player, -c.salary)),
        locked_card_keys=set(locked_cards),
        locked_golfer_set=set(locked_golfers),
        excluded_player_set=set(excluded_players),
        **_db_template_vars(),
    )
