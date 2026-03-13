# Roadmap: GB Golf Optimizer

## Overview

This roadmap delivers a working fantasy golf lineup optimizer in three phases, ordered by the dependency chain: validated data in, correct optimization, usable output. Phase 1 builds the data ingestion and validation layer (CSV parsing, card model, contest config) -- because the optimizer is only as good as its inputs. Phase 2 builds the ILP optimization engine with all GameBlazers-specific constraints (salary ranges, collection limits, cross-lineup card exclusion, cash-first priority). Phase 3 wires everything to a web UI via FastAPI/Jinja2 and deploys to the VPS. Each phase produces independently testable, verifiable output.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Data Foundation** - CSV parsing, card data model, projections merging, contest config, and data validation
- [ ] **Phase 2: Optimization Engine** - ILP lineup generation with salary, collection, and card exclusion constraints
- [ ] **Phase 3: Web Application and Deployment** - FastAPI endpoints, lineup display UI, and VPS deployment

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
**Plans**: TBD

Plans:
- [ ] 01-01: TBD
- [ ] 01-02: TBD

### Phase 2: Optimization Engine
**Goal**: Given validated cards and contest config, the optimizer produces correct optimal lineups for both contests with all constraints satisfied
**Depends on**: Phase 1
**Requirements**: OPT-01, OPT-02, OPT-03, OPT-04, OPT-06
**Success Criteria** (what must be TRUE):
  1. Optimizer generates 3 Tips lineups (6 golfers each) that maximize total effective value while respecting salary floor/cap and collection limits
  2. Optimizer generates 2 Intermediate Tee lineups (5 golfers each) using only cards not assigned to any Tips lineup
  3. No card appears in more than one lineup across all contests
  4. Optimizer returns a clear infeasibility message (not a crash) when constraints cannot be satisfied with the available card pool
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD

### Phase 3: Web Application and Deployment
**Goal**: Users interact with the optimizer through a browser -- upload files, trigger optimization, and view lineups -- on a live server
**Depends on**: Phase 2
**Requirements**: DISP-01, DISP-02, DEPL-01
**Success Criteria** (what must be TRUE):
  1. User can upload roster and projections CSVs through a web form and trigger lineup generation
  2. Generated lineups are displayed in the browser grouped by contest, showing player name, collection, salary, multiplier, projected score, and lineup totals
  3. Unmatched-player report is visible in the UI so users can identify data gaps before trusting results
  4. App is accessible at silverreyes.net (or subdomain) on the Hostinger KVM 2 VPS
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data Foundation | 0/0 | Not started | - |
| 2. Optimization Engine | 0/0 | Not started | - |
| 3. Web Application and Deployment | 0/0 | Not started | - |

---
*Roadmap created: 2026-03-13*
*Last updated: 2026-03-13*
