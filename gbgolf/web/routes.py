"""
Flask blueprint: index route handling file uploads and lineup generation.
"""
import json
import os
import tempfile
from datetime import date, datetime, timezone

from flask import Blueprint, current_app, render_template, request, session
from sqlalchemy import text

from gbgolf.data import validate_pipeline, validate_pipeline_auto, validate_pipeline_hybrid
from gbgolf.data.models import Card
from gbgolf.db import db
from gbgolf.optimizer import optimize
from gbgolf.optimizer.constraints import ConstraintSet, check_conflicts, check_feasibility


def _parse_entry_overrides(form, contests):
    """Parse 'entries_<index>' form fields into a dict keyed by contest name.

    Values are clamped to [0, contest.max_entries]. Missing or non-integer
    fields are skipped (the optimizer falls back to max_entries for those).
    """
    overrides = {}
    for idx, c in enumerate(contests):
        raw = form.get(f"entries_{idx}")
        if raw is None or raw == "":
            continue
        try:
            n = int(raw)
        except (ValueError, TypeError):
            continue
        overrides[c.name] = max(0, min(n, c.max_entries))
    return overrides


def _fmt_time(dt: datetime) -> str:
    """Format time as '1:30 PM' — cross-platform (no %-I)."""
    return dt.strftime("%I:%M %p").lstrip("0")


def _fmt_month_day(dt: datetime) -> str:
    """Format date as 'Apr 7' — cross-platform (no %-d)."""
    return f"{dt.strftime('%b')} {dt.day}"


def _serialize_cards(cards: list) -> str:
    """Serialize a list of Card objects to JSON for the hidden form field."""
    return json.dumps([
        {
            "player": c.player,
            "salary": c.salary,
            "multiplier": c.multiplier,
            "collection": c.collection,
            "expires": c.expires.isoformat() if c.expires else None,
            "instance_id": c.instance_id,
            "projected_score": c.projected_score,
            "effective_value": c.effective_value,
            "franchise": c.franchise,
            "rookie": c.rookie,
        }
        for c in cards
    ])


def _deserialize_cards(json_str: str) -> list:
    """Reconstruct Card objects from a JSON string. Returns list[Card].

    Every card payload must carry an ``instance_id`` field. Stale session data
    from before this field existed is rejected with a ``ValueError`` so the
    route handler can show the user a clear stale-session message instead of
    silently fabricating IDs that could collide with real ones.
    """
    raw = json.loads(json_str)
    cards = []
    for idx, d in enumerate(raw):
        if "instance_id" not in d:
            raise ValueError(
                f"Card payload at index {idx} is missing 'instance_id' "
                f"(stale session data; please re-upload the roster)"
            )
        expires = None
        if d.get("expires"):
            expires = date.fromisoformat(d["expires"])
        cards.append(Card(
            player=d["player"],
            salary=int(d["salary"]),
            multiplier=float(d["multiplier"]),
            collection=d["collection"],
            expires=expires,
            instance_id=int(d["instance_id"]),
            projected_score=d.get("projected_score"),
            effective_value=d.get("effective_value"),
            franchise=d.get("franchise", ""),
            rookie=d.get("rookie", ""),
        ))
    return cards


def _get_latest_fetch():
    """Query latest fetch record for staleness label. Returns dict or None."""
    row = db.session.execute(
        text("SELECT tournament_name, fetched_at, datagolf_updated_at FROM fetches ORDER BY fetched_at DESC LIMIT 1")
    ).mappings().fetchone()
    if row is None:
        return None
    fetched_at = row["fetched_at"]
    # SQLite returns datetime as string; PostgreSQL returns datetime object
    if isinstance(fetched_at, str):
        fetched_at = datetime.fromisoformat(fetched_at)
    now = datetime.now(timezone.utc)
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)
    delta = now - fetched_at
    fetched_at_local = fetched_at.astimezone()

    dg_updated_str = None
    dg_ua = row["datagolf_updated_at"]
    if dg_ua is not None:
        if isinstance(dg_ua, str):
            dg_ua = datetime.fromisoformat(dg_ua)
        if dg_ua.tzinfo is None:
            dg_ua = dg_ua.replace(tzinfo=timezone.utc)
        dg_ua_local = dg_ua.astimezone()
        dg_delta = now - dg_ua
        if dg_delta.days == 0:
            dg_updated_str = f"DG updated today at {_fmt_time(dg_ua_local)}"
        elif dg_delta.days == 1:
            dg_updated_str = f"DG updated yesterday at {_fmt_time(dg_ua_local)}"
        else:
            dg_updated_str = f"DG updated {_fmt_month_day(dg_ua_local)} at {_fmt_time(dg_ua_local)}"

    return {
        "tournament_name": row["tournament_name"],
        "days_ago": delta.days,
        "is_stale": delta.days >= 7,
        "fetched_time": _fmt_time(fetched_at_local),
        "fetched_date": _fmt_month_day(fetched_at_local),
        "dg_updated_str": dg_updated_str,
        "fetched_at_iso": fetched_at.isoformat(),
        "dg_updated_at_iso": dg_ua.isoformat() if dg_ua is not None else None,
    }


def _db_template_vars():
    """Return dict of DB-related template variables for render_template()."""
    latest_fetch = _get_latest_fetch()
    return {
        "latest_fetch": latest_fetch,
        "db_has_projections": latest_fetch is not None,
    }


bp = Blueprint("main", __name__)


@bp.route("/changelog", methods=["GET"])
def changelog():
    """Render CHANGELOG.md as HTML. Read-only; no DB access required."""
    import markdown as _md

    from gbgolf.changelog import read_changelog_text

    raw = read_changelog_text()
    html = _md.markdown(raw, extensions=["sane_lists"]) if raw else (
        "<p>Changelog unavailable.</p>"
    )
    return render_template("changelog.html", changelog_html=html)


@bp.route("/", methods=["GET", "POST"])
def index():
    """Main page: upload form (GET) and optimization results (POST)."""
    if request.method == "GET":
        return render_template(
            "index.html",
            contests=current_app.config["CONTESTS"],
            **_db_template_vars(),
        )

    # --- POST: handle file uploads ---
    roster_file = request.files.get("roster")
    if not roster_file or roster_file.filename == "":
        return render_template(
            "index.html",
            error="Roster file is required.",
            contests=current_app.config["CONTESTS"],
            **_db_template_vars(),
        )

    projection_source = request.form.get("projection_source", "csv")

    # Validate: projections file required for CSV and hybrid sources
    projections_file = request.files.get("projections")
    if projection_source in ("csv", "hybrid") and (not projections_file or projections_file.filename == ""):
        return render_template(
            "index.html",
            error="Projections file is required.",
            contests=current_app.config["CONTESTS"],
            **_db_template_vars(),
        )

    contests = current_app.config["CONTESTS"]
    entry_overrides = _parse_entry_overrides(request.form, contests)

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
        elif projection_source == "hybrid":
            if not projections_file or projections_file.filename == "":
                return render_template(
                    "index.html",
                    error="Projections file is required.",
                    contests=contests,
                    **_db_template_vars(),
                )
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="wb") as pf:
                projections_file.save(pf)
                projections_tmp = pf.name
            validation = validate_pipeline_hybrid(roster_tmp, projections_tmp, config_path)
        else:
            if not projections_file:
                return render_template(
                    "index.html",
                    error="Projections file is required.",
                    contests=contests,
                    **_db_template_vars(),
                )
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="wb") as pf:
                projections_file.save(pf)
                projections_tmp = pf.name
            validation = validate_pipeline(roster_tmp, projections_tmp, config_path)

        result = optimize(
            validation.valid_cards,
            contests,
            constraints=constraints,
            entry_overrides=entry_overrides,
        )

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
            contests=contests,
            entry_overrides=entry_overrides,
            **_db_template_vars(),
        )

    except ValueError as exc:
        return render_template(
            "index.html",
            error=str(exc),
            contests=contests,
            **_db_template_vars(),
        )

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

    contests = current_app.config["CONTESTS"]
    entry_overrides = _parse_entry_overrides(request.form, contests)

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

    for contest_config in contests:
        feasibility_result = check_feasibility(constraints, valid_cards, contest_config)
        if feasibility_result is not None:
            return render_template(
                "index.html",
                error=feasibility_result.message,
                show_results=False,
                card_pool_json=card_pool_json,
                contests=contests,
                entry_overrides=entry_overrides,
                **_db_template_vars(),
            )

    result = optimize(
        valid_cards,
        contests,
        constraints=constraints,
        entry_overrides=entry_overrides,
    )

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
        contests=contests,
        entry_overrides=entry_overrides,
        **_db_template_vars(),
    )
