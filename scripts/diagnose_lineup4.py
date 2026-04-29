"""
Diagnostic script: trace why the optimizer reports infeasibility on the 4th
Intermediate Tee lineup.

Read-only. Imports gbgolf modules but modifies nothing. Prints findings to stdout.

Usage:
    python -m scripts.diagnose_lineup4 --csv path/to/roster.csv [--projections-mode auto]
    python -m scripts.diagnose_lineup4 --csv roster.csv --projections-mode hybrid --projections-csv projections.csv
    python -m scripts.diagnose_lineup4 --csv roster.csv --projections-mode csv --projections-csv projections.csv

The 5 hypotheses being tested:
    1. Pool depletion (pre-check)         - len(available) < roster_size
    2. Solver infeasibility               - pool sufficient but constraints conflict
    3. Upstream filtering                 - card removed by apply_filters()
    4. Cross-contest depletion            - card consumed by The Tips
    5. Composite-key collision            - two distinct platform cards share one key
"""
import argparse
import os
import sys
from collections import Counter
from dataclasses import dataclass

import pulp

# Make sure project root is importable when run as `python scripts/diagnose_lineup4.py`
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from gbgolf.data import (  # noqa: E402
    validate_pipeline,
    validate_pipeline_auto,
    validate_pipeline_hybrid,
    load_config,
)
from gbgolf.data.roster import parse_roster_csv  # noqa: E402
from gbgolf.optimizer import optimize, _card_key  # noqa: E402
from gbgolf.optimizer.engine import _solve_one_lineup  # noqa: E402


def _resolve_config_path(override: str | None) -> str:
    """Find contest_config.json. Order: CLI override, CWD, alongside script's parent."""
    if override:
        return override
    candidates = [
        os.path.join(os.getcwd(), "contest_config.json"),
        os.path.join(PROJECT_ROOT, "contest_config.json"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    sys.exit(
        "Could not find contest_config.json. Tried:\n  "
        + "\n  ".join(candidates)
        + "\nPass --config <path> to override."
    )


# ---------------------------------------------------------------------------
# Known-feasible lineup 4 (from user's manual entry on the platform)
# ---------------------------------------------------------------------------
# Composite key tuple: (player_name, salary, multiplier, collection)
# Collection is unknown from the screenshot alone; the script tries to match
# on (player, salary, multiplier) and reports whichever collection it finds.
KNOWN_LINEUP_4 = [
    {"player": "Si Woo Kim",       "salary": 11040, "multiplier": 1.2},
    {"player": "Min Woo Lee",      "salary": 11180, "multiplier": 1.3},
    {"player": "Hideki Matsuyama", "salary": 9900,  "multiplier": 1.1},
    {"player": "Justin Rose",      "salary": 8700,  "multiplier": 1.0},
    {"player": "Sam Stevens",      "salary": 10950, "multiplier": 1.5},
]


# ---------------------------------------------------------------------------
# Pretty-printing helpers
# ---------------------------------------------------------------------------

def hdr(title: str) -> None:
    print()
    print("=" * 78)
    print(f"  {title}")
    print("=" * 78)


def sub(title: str) -> None:
    print()
    print("-" * 78)
    print(f"  {title}")
    print("-" * 78)


def fmt_card(c) -> str:
    return f"{c.player!r:<28} salary=${c.salary:<6} x{c.multiplier:<4} coll={c.collection!r}"


def fmt_key(k: tuple) -> str:
    p, s, m, coll = k
    return f"{p!r} ${s} x{m} {coll!r}"


# ---------------------------------------------------------------------------
# Steps 1-2: load data, trace known cards through the pipeline
# ---------------------------------------------------------------------------

def load_pipeline(args):
    """Run the same validation pipeline the web app uses. Returns (raw_rows, vr, contests)."""
    # raw_rows preserves what the CSV actually contained, before filters
    raw_rows = parse_roster_csv(args.csv)
    config_path = _resolve_config_path(args.config)
    contests = load_config(config_path)

    if args.projections_mode == "auto":
        # auto mode reads from DB - need Flask app context
        from gbgolf.web import create_app
        app = create_app()
        with app.app_context():
            vr = validate_pipeline_auto(args.csv, config_path)
    elif args.projections_mode == "hybrid":
        if not args.projections_csv:
            sys.exit("--projections-csv is required for hybrid mode")
        from gbgolf.web import create_app
        app = create_app()
        with app.app_context():
            vr = validate_pipeline_hybrid(args.csv, args.projections_csv, config_path)
    elif args.projections_mode == "csv":
        if not args.projections_csv:
            sys.exit("--projections-csv is required for csv mode")
        vr = validate_pipeline(args.csv, args.projections_csv, config_path)
    else:
        sys.exit(f"unknown projections-mode: {args.projections_mode}")

    return raw_rows, vr, contests


def trace_known_cards(raw_rows, vr):
    """For each known lineup-4 card, report presence in raw CSV, valid_cards, excluded.

    Returns a list of trace dicts, one per known card.
    """
    sub("Step 2: tracing each known lineup-4 card through the data pipeline")

    traces = []
    for known in KNOWN_LINEUP_4:
        player = known["player"]
        salary = known["salary"]
        mult = known["multiplier"]

        # CSV matches: any row with this player+salary+multiplier (any collection)
        csv_matches = [
            c for c in raw_rows
            if c.player == player
            and c.salary == salary
            and abs(c.multiplier - mult) < 0.001
        ]

        # valid_cards matches
        valid_matches = [
            c for c in vr.valid_cards
            if c.player == player
            and c.salary == salary
            and abs(c.multiplier - mult) < 0.001
        ]

        # excluded matches (by player only - ExclusionRecord lacks salary/mult)
        excluded_matches = [e for e in vr.excluded if e.player == player]

        # Collisions: any other card sharing the SAME composite key (player, salary, mult, collection)
        collisions = []
        for vm in valid_matches:
            same_key = [c for c in raw_rows if _card_key(c) == _card_key(vm)]
            if len(same_key) > 1:
                collisions.append((vm, len(same_key)))

        trace = {
            "known": known,
            "csv_count": len(csv_matches),
            "csv_collections": sorted({c.collection for c in csv_matches}),
            "valid_count": len(valid_matches),
            "valid_card": valid_matches[0] if valid_matches else None,
            "excluded_reasons": sorted({e.reason for e in excluded_matches}),
            "collisions": collisions,
        }
        traces.append(trace)

        print()
        print(f"  Card: {player!r}  ${salary}  x{mult}")
        print(f"    in CSV:          {trace['csv_count']} row(s)"
              + (f"  collections={trace['csv_collections']}" if csv_matches else ""))
        print(f"    in valid_cards:  {trace['valid_count']} card(s)"
              + (f"  -> {fmt_card(trace['valid_card'])}" if trace['valid_card'] else ""))
        if trace["excluded_reasons"]:
            print(f"    excluded reasons (any salary/mult, this player): "
                  f"{trace['excluded_reasons']}")
        if trace["collisions"]:
            for vm, n in trace["collisions"]:
                print(f"    !! COMPOSITE-KEY COLLISION: {fmt_card(vm)} matches {n} CSV rows")

    return traces


# ---------------------------------------------------------------------------
# Step 3: run optimize() to confirm we reproduce the infeasibility
# ---------------------------------------------------------------------------

def run_optimizer(vr, contests):
    sub("Step 3: running optimize() to reproduce the infeasibility")

    result = optimize(vr.valid_cards, contests)

    for cname, lineups in result.lineups.items():
        print(f"  {cname}: {len(lineups)} lineup(s) built")
        for i, lu in enumerate(lineups, 1):
            players = ", ".join(c.player for c in lu.cards)
            print(f"    [{i}] salary=${lu.total_salary:<6} EV={lu.total_effective_value:.2f}  {players}")

    print()
    if result.infeasibility_notices:
        print("  Infeasibility notices:")
        for n in result.infeasibility_notices:
            print(f"    - {n}")
    else:
        print("  No infeasibility notices reported.")

    return result


# ---------------------------------------------------------------------------
# Step 4: replay the Phase 1 loop locally with full instrumentation
# ---------------------------------------------------------------------------

@dataclass
class AttemptRecord:
    contest: str
    lineup_num: int
    pool_size: int
    pool_unique_players: int
    salary_min: int
    salary_max: int
    salary_mean: int
    collection_breakdown: dict
    used_keys_at_start: int
    solver_status: str
    failed_at: str | None
    selected_cards: list  # list[Card] or empty
    available_keys_at_attempt: set  # set of composite keys


def replay_phase1(vr, contests):
    """Re-implement Phase 1 of optimize() locally with print instrumentation.

    Mirrors gbgolf/optimizer/__init__.py lines 173-191 exactly. Calls the
    imported _solve_one_lineup and _card_key (no monkey-patching).

    Returns (records, lineups_by_contest, used_card_keys_per_attempt).
    """
    sub("Step 4: replaying Phase 1 with instrumentation")

    used_card_keys: set = set()
    used_by: dict[tuple, str] = {}  # composite key -> "<contest>:<slot>" that consumed it

    records: list[AttemptRecord] = []
    lineups_by_contest: dict[str, list] = {c.name: [] for c in contests}
    snapshots: list[set] = []  # used_card_keys snapshot at each attempt

    for config in contests:
        n_entries = config.max_entries
        print()
        print(f"  >>> Contest: {config.name}  (max_entries={n_entries}, "
              f"roster_size={config.roster_size}, salary [{config.salary_min}-{config.salary_max}])")

        for entry_num in range(n_entries):
            # mirror line 175-180 of __init__.py
            available = [c for c in vr.valid_cards if _card_key(c) not in used_card_keys]
            avail_keys = {_card_key(c) for c in available}
            snapshot = set(used_card_keys)
            snapshots.append(snapshot)

            salaries = [c.salary for c in available]
            colls = Counter(c.collection for c in available)
            unique_players = len({c.player for c in available})

            print()
            print(f"    Lineup {entry_num + 1} of {n_entries}:")
            print(f"      pool size:     {len(available)}")
            print(f"      unique golfers: {unique_players}")
            if salaries:
                print(f"      salary range:  ${min(salaries)} - ${max(salaries)}  "
                      f"(mean ${sum(salaries) // len(salaries)})")
            print(f"      collections:   {dict(colls)}")
            print(f"      used so far:   {len(used_card_keys)} card key(s)")

            # Pre-check (mirrors engine.py:36)
            if not available or len(available) < config.roster_size:
                rec = AttemptRecord(
                    contest=config.name,
                    lineup_num=entry_num + 1,
                    pool_size=len(available),
                    pool_unique_players=unique_players,
                    salary_min=min(salaries) if salaries else 0,
                    salary_max=max(salaries) if salaries else 0,
                    salary_mean=sum(salaries) // len(salaries) if salaries else 0,
                    collection_breakdown=dict(colls),
                    used_keys_at_start=len(used_card_keys),
                    solver_status="pre_check_too_few_cards",
                    failed_at="pre_check",
                    selected_cards=[],
                    available_keys_at_attempt=avail_keys,
                )
                records.append(rec)
                print(f"      RESULT:        FAILED at pre-check "
                      f"(need {config.roster_size}, have {len(available)})")
                continue

            # Replay the actual solve, capturing PuLP status. We re-build the
            # ILP locally (cloned from engine.py) so we can read prob.status
            # without modifying engine.py.
            status = _replay_solve_status(available, config)

            # Use the production _solve_one_lineup to get the actual selection
            # (this guarantees we match production behavior exactly).
            result_cards = _solve_one_lineup(available, config)

            if result_cards is None:
                rec = AttemptRecord(
                    contest=config.name,
                    lineup_num=entry_num + 1,
                    pool_size=len(available),
                    pool_unique_players=unique_players,
                    salary_min=min(salaries),
                    salary_max=max(salaries),
                    salary_mean=sum(salaries) // len(salaries),
                    collection_breakdown=dict(colls),
                    used_keys_at_start=len(used_card_keys),
                    solver_status=status,
                    failed_at="solver",
                    selected_cards=[],
                    available_keys_at_attempt=avail_keys,
                )
                records.append(rec)
                print(f"      RESULT:        FAILED at solver (PuLP status: {status})")
                continue

            # Success - mark cards used, mirror line 189-191
            for card in result_cards:
                k = _card_key(card)
                used_card_keys.add(k)
                used_by[k] = f"{config.name}:lineup-{entry_num + 1}"
            lineups_by_contest[config.name].append(result_cards)

            rec = AttemptRecord(
                contest=config.name,
                lineup_num=entry_num + 1,
                pool_size=len(available),
                pool_unique_players=unique_players,
                salary_min=min(salaries),
                salary_max=max(salaries),
                salary_mean=sum(salaries) // len(salaries),
                collection_breakdown=dict(colls),
                used_keys_at_start=len(used_card_keys) - len(result_cards),
                solver_status=status,
                failed_at=None,
                selected_cards=list(result_cards),
                available_keys_at_attempt=avail_keys,
            )
            records.append(rec)
            total_salary = sum(c.salary for c in result_cards)
            ev = sum((c.effective_value or 0.0) for c in result_cards)
            print(f"      RESULT:        OK  salary=${total_salary}  EV={ev:.2f}")
            print(f"      selected:      {[c.player for c in result_cards]}")

    return records, lineups_by_contest, used_by, snapshots


def _replay_solve_status(cards, config):
    """Clone of _solve_one_lineup that returns the PuLP status string only.

    Mirrors gbgolf/optimizer/engine.py exactly (no lock paths since Phase 1
    has no locks).
    """
    if not cards or len(cards) < config.roster_size:
        return "pre_check_too_few_cards"

    n = len(cards)
    prob = pulp.LpProblem("lineup_diag", pulp.LpMaximize)
    x = [pulp.LpVariable(f"x_{i}", cat="Binary") for i in range(n)]
    prob += pulp.lpSum((cards[i].effective_value or 0.0) * x[i] for i in range(n))
    prob += pulp.lpSum(x[i] for i in range(n)) == config.roster_size
    prob += pulp.lpSum(cards[i].salary * x[i] for i in range(n)) >= config.salary_min
    prob += pulp.lpSum(cards[i].salary * x[i] for i in range(n)) <= config.salary_max
    for coll_name, limit in config.collection_limits.items():
        eligible = [i for i, c in enumerate(cards) if c.collection == coll_name]
        if eligible:
            prob += pulp.lpSum(x[i] for i in eligible) <= limit
    player_to_indices = {}
    for i, c in enumerate(cards):
        player_to_indices.setdefault(c.player, []).append(i)
    for _player, indices in player_to_indices.items():
        if len(indices) > 1:
            prob += pulp.lpSum(x[i] for i in indices) <= 1
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    return pulp.LpStatus[prob.status]


# ---------------------------------------------------------------------------
# Step 5: cross-reference known cards against pool state at lineup 4
# ---------------------------------------------------------------------------

def cross_reference(traces, records, used_by, snapshots, contests):
    """For each known card, report its status at the moment lineup 4 was attempted."""
    sub("Step 5: cross-reference known lineup-4 cards against pool state at attempt")

    # Find the record for The Intermediate Tee lineup 4 (or whichever lineup failed)
    intermediate_attempts = [r for r in records if r.contest == "The Intermediate Tee"]
    if not intermediate_attempts:
        print("  No Intermediate Tee attempts recorded - cannot cross-reference.")
        return None

    # Find the first failed attempt (or the last attempt if all succeeded)
    failed = [r for r in intermediate_attempts if r.failed_at is not None]
    if failed:
        target = failed[0]
        print(f"  Target attempt: {target.contest} lineup {target.lineup_num} "
              f"(failed at {target.failed_at}, status={target.solver_status})")
    else:
        target = intermediate_attempts[-1]
        print(f"  No Intermediate failures - reporting state at last attempt: "
              f"lineup {target.lineup_num}")

    # Reconstruct the snapshot of used_card_keys at the moment this attempt began
    target_idx = records.index(target)
    snapshot_at_attempt = snapshots[target_idx]

    # For each known card, determine its status
    print()
    verdict_per_card = []
    for trace in traces:
        known = trace["known"]
        label = f"{known['player']!r} ${known['salary']} x{known['multiplier']}"

        if trace["valid_count"] == 0:
            if trace["csv_count"] == 0:
                print(f"  {label}")
                print(f"    -> NOT IN CSV  (hypothesis 3 candidate, but actually missing roster row)")
                verdict_per_card.append(("missing_csv", trace))
            else:
                print(f"  {label}")
                print(f"    -> IN CSV but NOT in valid_cards")
                print(f"       excluded reasons (this player): {trace['excluded_reasons']}")
                verdict_per_card.append(("filtered_upstream", trace))
            continue

        valid_card = trace["valid_card"]
        k = _card_key(valid_card)

        # Composite-key collision: user owns multiple copies of this card
        # (CSV has 2+ rows with identical (player, salary, multiplier, collection)).
        # Under the buggy composite-key tracking, ALL copies look "consumed" once
        # one is used. This is hypothesis 5 in the plan — and the dominant cause
        # if collisions are present.
        is_collision = trace["csv_count"] > 1

        if k in snapshot_at_attempt:
            consumer = used_by.get(k, "unknown")
            print(f"  {label}  coll={valid_card.collection!r}")
            print(f"    -> already CONSUMED by {consumer} at the moment lineup 4 was attempted")
            if is_collision:
                print(f"       (BUT user owns {trace['csv_count']} copies — the second copy "
                      f"would be available under instance-based tracking)")
                verdict_per_card.append(("composite_key_collision", trace))
            elif consumer.startswith("The Tips:"):
                verdict_per_card.append(("cross_contest_depletion", trace))
            else:
                verdict_per_card.append(("intra_contest_depletion", trace))
        else:
            print(f"  {label}  coll={valid_card.collection!r}")
            print(f"    -> AVAILABLE in the pool at lineup 4 attempt")
            verdict_per_card.append(("available", trace))

    return target, verdict_per_card


# ---------------------------------------------------------------------------
# Final verdict
# ---------------------------------------------------------------------------

def print_verdict(target, verdicts, traces):
    hdr("VERDICT")

    if target is None:
        print("  Could not determine target attempt. Inspect output above.")
        return

    if target.failed_at is None:
        print("  Target attempt did NOT fail in this run. The infeasibility")
        print("  was not reproduced. Re-check inputs (CSV + projections mode).")
        return

    print(f"  Target failure: {target.contest} lineup {target.lineup_num}")
    print(f"  failed_at:      {target.failed_at}")
    print(f"  solver_status:  {target.solver_status}")
    print(f"  pool size:      {target.pool_size}  (need {5})")
    print(f"  unique golfers: {target.pool_unique_players}")
    print(f"  collections:    {target.collection_breakdown}")
    print()

    counts = Counter(v[0] for v in verdicts)
    print(f"  Known-card statuses:  {dict(counts)}")
    print()

    # Map to hypotheses (priority order: collisions dominate over depletion
    # because depletion of a card the user owns 2+ copies of is the SYMPTOM of
    # the collision bug, not an independent cause).
    if "missing_csv" in counts:
        print("  HYPOTHESIS: the user's manual lineup uses cards NOT in the uploaded")
        print("  CSV. The diagnostic CSV may differ from the one used in production.")
    elif "filtered_upstream" in counts:
        print("  HYPOTHESIS 3: UPSTREAM FILTERING")
        print("  One or more lineup-4 cards were dropped by apply_filters() before")
        print("  reaching the optimizer. Most likely cause: 'no projection found'")
        print("  for one of these golfers in the projections source.")
    elif "composite_key_collision" in counts:
        print("  HYPOTHESIS 5: COMPOSITE-KEY COLLISION")
        print("  The user owns duplicate cards (multiple CSV rows with identical")
        print("  player+salary+multiplier+collection). Under composite-key tracking,")
        print("  consuming one copy makes ALL copies invisible. Under instance-id")
        print("  tracking, each copy is independently usable.")
    elif "cross_contest_depletion" in counts:
        print("  HYPOTHESIS 4: CROSS-CONTEST DEPLETION")
        print("  One or more lineup-4 cards were consumed by The Tips lineups.")
        print("  The shared used_instance_ids set across contests is the cause.")
    elif "intra_contest_depletion" in counts:
        print("  HYPOTHESIS 1 or 4 (intra-contest variant):")
        print("  Lineup-4 cards were consumed by EARLIER Intermediate Tee lineups")
        print("  (1, 2, or 3). The greedy sequential allocation reached a state")
        print("  where the manual lineup is no longer reachable.")
    elif counts.get("available", 0) == len(traces):
        print("  HYPOTHESIS 2: SOLVER INFEASIBILITY (UNEXPECTED)")
        print("  All 5 manual-lineup-4 cards are available in the pool at the moment")
        print("  lineup 4 is attempted, but the solver still returns infeasible.")
        print("  This is contradictory and indicates a deeper bug. Re-check:")
        print("    - collection_limits values vs. actual collection names in CSV")
        print("    - whether multiple cards in the pool share the same composite key")
        print("    - the salary_max constraint vs. the pool's mean salary")
    else:
        print("  Mixed verdicts. Inspect Step 5 output to resolve.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--csv", required=True, help="Path to GameBlazers roster CSV")
    p.add_argument("--projections-mode", default="auto",
                   choices=["auto", "hybrid", "csv"],
                   help="Projection source (default: auto, matches web app default)")
    p.add_argument("--projections-csv", default=None,
                   help="Path to projections CSV (required for hybrid or csv modes)")
    p.add_argument("--config", default=None,
                   help="Path to contest_config.json (default: search CWD, then project root)")
    args = p.parse_args()

    if not os.path.exists(args.csv):
        sys.exit(f"CSV not found: {args.csv}")

    hdr("STEP 1: Load data via the same pipeline the web app uses")
    raw_rows, vr, contests = load_pipeline(args)
    print(f"  Roster CSV rows:       {len(raw_rows)}")
    print(f"  Valid cards:           {len(vr.valid_cards)}")
    print(f"  Excluded:              {len(vr.excluded)}")
    if vr.excluded:
        ex_counts = Counter(e.reason for e in vr.excluded)
        for reason, count in ex_counts.most_common():
            print(f"    {reason}: {count}")
    print(f"  Projection warnings:   {len(vr.projection_warnings)}")
    print(f"  Contests:              {[c.name for c in contests]}")

    traces = trace_known_cards(raw_rows, vr)

    run_optimizer(vr, contests)

    records, lineups_by_contest, used_by, snapshots = replay_phase1(vr, contests)

    target, verdicts = cross_reference(traces, records, used_by, snapshots, contests)

    print_verdict(target, verdicts, traces)


if __name__ == "__main__":
    main()
