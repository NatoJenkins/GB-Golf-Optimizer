# Retrospective: GB Golf Optimizer

---

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-13
**Phases:** 3 | **Plans:** 10

### What Was Built

- CSV ingestion pipeline with NFKD name normalization and projection merging
- ILP optimizer (PuLP/CBC) enforcing salary ranges, collection limits, same-player and cross-contest card locking
- Flask web app with dual-CSV upload, lineup tables by contest, and unmatched player report
- Systemd + Nginx deployment config for Hostinger KVM 2 VPS
- Live app deployed and browser-verified at gameblazers.silverreyes.net/golf

### What Worked

- **TDD RED→GREEN discipline**: Every phase scaffolded failing stubs first, then implemented to green. Caught real bugs (test fixture undersizing in 02-03).
- **Pydantic at boundary only**: Validated external JSON at I/O, passed plain dataclasses internally — kept optimizer layer clean and fast.
- **Dependency chain ordering**: Data → Optimizer → Web/Deploy was the natural order; each phase produced independently testable output consumed by the next.
- **Pure formatting functions**: `report.py` returning strings instead of printing kept formatters testable and the CLI layer thin.
- **ILP upper-bound-only collection constraints**: Realized early that 0 Weekly Collection cards per lineup is legal — avoids infeasibility for edge-case pools.

### What Was Inefficient

- **Test fixture undersizing**: Phase 02-03 required expanding `TIPS_CARDS` (12→18) and `ALL_CARDS` (25→35) because initial fixtures couldn't satisfy disjoint pool requirements for multiple lineups. This was caught by tests but required rework.
- **Blockers listed in STATE.md that were already resolved**: Franchise/Rookie and same-golfer constraints were flagged as open blockers but resolved in Phase 1 context-gathering.

### Patterns Established

- **NFKD Unicode normalization** for golfer name matching (`Åberg == Aberg`) — essential for international golfer names.
- **Windows-safe temp file pattern**: Write inside with-block, pass path outside after close — avoids `NamedTemporaryFile` locking on Windows dev machines.
- **SCRIPT_NAME via systemd environment variable**: Flask/Werkzeug reads it automatically — zero code changes needed to support URL prefix under `/golf`.
- **Pool-size guard in pipeline**: `validate_pipeline()` uses `min(c.roster_size)` to fail fast before optimizer receives unusable data.

### Key Lessons

- **Confirm domain rules early**: The Franchise/Rookie flag question and same-golfer-per-lineup rule both needed user confirmation. Getting these in Phase 1 context prevented backtracking in Phase 2.
- **ILP infeasibility is a feature**: Returning a clear notice (not crashing) when constraints can't be satisfied is UX-critical for a tool users will run weekly with different card pools.
- **Human verification phases are legitimate**: Phase 03-03 was a purely human step (deploy + browser confirm). No code written. Worth a dedicated plan for traceability.

### Cost Observations

- Sessions: 1 intense session (all 3 phases in ~8 hours)
- Notable: Single-day delivery of full stack including VPS deployment

---

## Cross-Milestone Trends

| Milestone | Phases | Plans | LOC | Days | Key Win |
|-----------|--------|-------|-----|------|---------|
| v1.0 MVP | 3 | 10 | 1,407 | 1 | TDD + ILP delivered working optimizer in one session |
