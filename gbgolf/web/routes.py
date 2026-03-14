"""
Flask blueprint: index route handling file uploads and lineup generation.
"""
import os
import tempfile

from flask import Blueprint, current_app, render_template, request, session

from gbgolf.data import validate_pipeline
from gbgolf.optimizer import optimize
from gbgolf.optimizer.constraints import ConstraintSet, check_conflicts, check_feasibility

bp = Blueprint("main", __name__)


@bp.route("/", methods=["GET", "POST"])
def index():
    """Main page: upload form (GET) and optimization results (POST)."""
    if request.method == "GET":
        return render_template("index.html")

    # --- POST: handle file uploads ---
    roster_file = request.files.get("roster")
    if not roster_file or roster_file.filename == "":
        return render_template("index.html", error="Roster file is required.")

    projections_file = request.files.get("projections")
    if not projections_file or projections_file.filename == "":
        return render_template("index.html", error="Projections file is required.")

    # CLEAR lock/exclude session keys on file upload (UI-04)
    # Unconditional — no hash comparison. Order: clear -> build -> optimize.
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
        # Write uploads to temp files (closed before passing to validate_pipeline
        # so Windows does not keep an exclusive lock on the file handle)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="wb") as rf:
            roster_file.save(rf)
            roster_tmp = rf.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="wb") as pf:
            projections_file.save(pf)
            projections_tmp = pf.name

        # Files are now closed; safe to read on Windows
        config_path = current_app.config["CONFIG_PATH"]
        validation = validate_pipeline(roster_tmp, projections_tmp, config_path)
        result = optimize(validation.valid_cards, current_app.config["CONTESTS"], constraints=constraints)

        return render_template(
            "index.html",
            validation=validation,
            result=result,
            show_results=True,
            lock_reset=lock_reset,
        )

    except ValueError as exc:
        return render_template("index.html", error=str(exc))

    finally:
        # Clean up temp files regardless of outcome
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
