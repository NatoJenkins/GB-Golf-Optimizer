# Changelog

All notable changes to GB Golf Optimizer are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.2] — 2026-04-29

### Fixed

- Duplicate cards (same player, salary, multiplier, collection) are now correctly tracked as separate instances. Users who own multiple copies of a card can now deploy each copy in a separate lineup, where previously the optimizer would consume both copies after one was used. This was the root cause of intermittent infeasibility in contests with larger lineup counts.
- Locking a card whose composite key matches multiple owned instances now correctly selects exactly one instance, rather than attempting to force both copies into the same lineup.

## [1.2.1] — 2026-04-28

### Added

- Per-contest lineup count selector on the upload and Re-Optimize forms. Each contest's `max_entries` is now an upper bound — submit fewer lineups for any contest by lowering its number before generating. Defaults to the cap, so existing behavior is unchanged unless you change it. Submitted values round-trip into the Re-Optimize form so they survive lock/exclude changes.

## [1.2.0] — initial tracked release

This entry summarizes the optimizer's state at the point changelog tracking began. Earlier history is in git.

### Added

- Automated projection ingestion via the DataGolf `fantasy-projection-defaults` API.
- Scheduled cron updates on Tuesdays and Wednesdays so projections are fresh ahead of each tournament.
- Three projection-source modes: Auto (DB-backed), Hybrid (CSV with DataGolf backfill), and Upload CSV (manual), with staleness warnings for older fetches.
- ILP-based lineup optimization (PuLP/CBC) with salary, roster size, collection, same-player, lock/exclude, and cross-contest disjointness constraints.
- Sub-500ms typical solve time across both contests on the production VPS.
