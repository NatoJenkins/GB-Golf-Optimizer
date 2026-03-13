"""
CLI entry point for the GB Golf Optimizer data layer.
Usage: python -m gbgolf.data validate roster.csv projections.csv [--config PATH] [--verbose]
"""
import argparse
import sys

from gbgolf.data import validate_pipeline
from gbgolf.data.report import format_exclusion_report, format_summary, format_verbose


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m gbgolf.data",
        description="Validate GB Golf Optimizer roster and projections input files.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    val = sub.add_parser("validate", help="Parse and validate input CSV files")
    val.add_argument("roster_csv", help="Path to GameBlazers roster export CSV")
    val.add_argument("projections_csv", help="Path to weekly projections CSV")
    val.add_argument(
        "--config",
        default="contest_config.json",
        help="Path to contest config JSON (default: contest_config.json)",
    )
    val.add_argument(
        "--verbose",
        action="store_true",
        help="Also list all valid cards with effective values",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "validate":
        try:
            result = validate_pipeline(
                args.roster_csv, args.projections_csv, args.config
            )
        except (ValueError, FileNotFoundError) as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)

        # Total parsed = valid + excluded (projection_warnings are not cards)
        total_parsed = len(result.valid_cards) + len(result.excluded)

        print(format_summary(result, total_parsed))
        print()

        if result.projection_warnings:
            print("Projection warnings:")
            for w in result.projection_warnings:
                print(f"  WARNING: {w}")
            print()

        print("Exclusion report:")
        print(format_exclusion_report(result.excluded))

        if args.verbose:
            print()
            print("Valid cards (sorted by effective value, descending):")
            print(format_verbose(result.valid_cards))


if __name__ == "__main__":
    main()
