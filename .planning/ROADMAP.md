# Roadmap: GB Golf Optimizer

## Overview

This roadmap delivers a working fantasy golf lineup optimizer in three phases, ordered by the dependency chain: validated data in, correct optimization, usable output. Phase 1 builds the data ingestion and validation layer (CSV parsing, card model, contest config) -- because the optimizer is only as good as its inputs. Phase 2 builds the ILP optimization engine with all GameBlazers-specific constraints (salary ranges, collection limits, cross-lineup card exclusion, cash-first priority). Phase 3 wires everything to a web UI via Flask/Jinja2 and deploys to the VPS. Each phase produces independently testable, verifiable output.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Data Foundation** - CSV parsing, card data model, projections merging, contest config, and data validation (completed 2026-03-13)
- [x] **Phase 2: Optimization Engine** - ILP lineup generation with salary, collection, and card exclusion constraints (completed 2026-03-14)
- [ ] **Phase 3: Web Application and Deployment** - Flask endpoints, lineup display UI, and VPS deployment

## Phase Details

### Phase 1: Data Foundation
**Goal**: User's raw CSV files are parsed into validated, projection-enriched card objects ready for optimization
**Depends on**: Nothing (first phase)
**Requirements**: UPLD-01, UPLD-02, OPT-05, OPT-07, DATA-01, DATA-02, DATA-03
**Success Criteria** (what must be TRUE):
  1. User can provide a GameBlazers roster CSV and get back a parsed set of cards with unique IDs, salaries, multipliers, and collection types
  2. User can provide a projections CSV and each card receives an effective value (projected_score x multiplier), with unmatched players surfaced in a report
  3. Cards with $0 salary or past expiration dates are automatically excluded from the card pool
  4. Contest parameters (salary ranges, roster sizes, collection limits) are loaded from an editable JSON config file
**Plans**: 4 plans

Plans:
- [ ] 01-01-PLAN.md — Project scaffold: pyproject.toml, gbgolf package skeleton, pytest test infrastructure with failing stubs
- [ ] 01-02-PLAN.md — Core parsers: Card model, roster CSV parser, projections CSV parser, name normalization and projection matching
- [ ] 01-03-PLAN.md — Filters and config: $0/expired/no-projection exclusion filters, Pydantic contest config loader, contest_config.json
- [ ] 01-04-PLAN.md — Pipeline integration: validate_pipeline() public API, CLI entry point, report formatting, human readability checkpoint

### Phase 2: Optimization Engine
**Goal**: Given validated cards and contest config, the optimizer produces correct optimal lineups for both contests with all constraints satisfied
**Depends on**: Phase 1
**Requirements**: OPT-01, OPT-02, OPT-03, OPT-04, OPT-06
**Success Criteria** (what must be TRUE):
  1. Optimizer generates 3 Tips lineups (6 golfers each) that maximize total effective value while respecting salary floor/cap and collection limits
  2. Optimizer generates 2 Intermediate Tee lineups (5 golfers each) using only cards not assigned to any Tips lineup
  3. No card appears in more than one lineup across all contests
  4. Optimizer returns a clear infeasibility message (not a crash) when constraints cannot be satisfied with the available card pool
**Plans**: 3 plans

Plans:
- [ ] 02-01-PLAN.md — Wave 0 scaffold: PuLP dependency, optimizer module skeleton (Lineup/OptimizationResult dataclasses, stubs), 10 failing test stubs
- [ ] 02-02-PLAN.md — ILP engine: implement _solve_one_lineup with roster size, salary range, collection limit, and same-player constraints using PuLP+CBC
- [ ] 02-03-PLAN.md — Sequential orchestrator: implement optimize() driving sequential solves across contests with pool mutation, partial results, and infeasibility notices

### Phase 3: Web Application and Deployment
**Goal**: Users interact with the optimizer through a browser -- upload files, trigger optimization, and view lineups -- on a live server
**Depends on**: Phase 2
**Requirements**: DISP-01, DISP-02, DEPL-01
**Success Criteria** (what must be TRUE):
  1. User can upload roster and projections CSVs through a web form and trigger lineup generation
  2. Generated lineups are displayed in the browser grouped by contest, showing player name, collection, salary, multiplier, projected score, and lineup totals
  3. Unmatched-player report is visible in the UI so users can identify data gaps before trusting results
  4. App is accessible at silverreyes.net (or subdomain) on the Hostinger KVM 2 VPS
**Plans**: 3 plans

Plans:
- [ ] 03-01-PLAN.md — Flask web app: test stubs + TDD implementation of gbgolf/web/ package (app factory, routes, Jinja2 template, CSS) and wsgi.py entry point
- [ ] 03-02-PLAN.md — Deployment config: systemd service unit, Nginx server block, step-by-step DEPLOY.md for VPS setup
- [ ] 03-03-PLAN.md — Human verification: user deploys to VPS and confirms live app at gameblazers.silverreyes.net/golf

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data Foundation | 4/4 | Complete   | 2026-03-13 |
| 2. Optimization Engine | 3/3 | Complete   | 2026-03-14 |
| 3. Web Application and Deployment | 0/3 | Not started | - |

---
*Roadmap created: 2026-03-13*
*Last updated: 2026-03-14*
