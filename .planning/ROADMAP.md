# Roadmap: GB Golf Optimizer

## Milestones

- ✅ **v1.0 MVP** — Phases 1–3 (shipped 2026-03-13)
- 🚧 **v1.1 Manual Lock/Exclude** — Phases 4–7 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1–3) — SHIPPED 2026-03-13</summary>

- [x] Phase 1: Data Foundation (4/4 plans) — completed 2026-03-13
- [x] Phase 2: Optimization Engine (3/3 plans) — completed 2026-03-13
- [x] Phase 3: Web Application and Deployment (3/3 plans) — completed 2026-03-13

See: `.planning/milestones/v1.0-ROADMAP.md` for full phase details.

</details>

### 🚧 v1.1 Manual Lock/Exclude (In Progress)

**Milestone Goal:** Users can force specific cards or golfers in or out of optimization after uploading CSVs, and re-optimize iteratively within a session without re-uploading files.

- [x] **Phase 4: Constraint Foundation** — Stable card identity, lock/exclude ILP constraints, pre-solve diagnostics, and session reset (completed 2026-03-14)
- [x] **Phase 5: Serialization and Re-Optimize Route** — Card serialization helpers and POST /reoptimize endpoint (completed 2026-03-14)
- [ ] **Phase 6: Lock/Exclude UI** — Player pool table with per-card controls, Re-Optimize button, and locked card markers in output
- [ ] **Phase 7: Polish** — Clear-all button and active lock/exclude count display

## Phase Details

### Phase 4: Constraint Foundation
**Goal**: The optimizer correctly enforces lock and exclude constraints, detects conflicts and infeasibility before solving, and clears stale state when new CSVs are uploaded
**Depends on**: Phase 3 (v1.0 complete)
**Requirements**: LOCK-01, LOCK-02, LOCK-03, LOCK-04, EXCL-01, EXCL-02, UI-04
**Success Criteria** (what must be TRUE):
  1. User can lock a specific card (player + multiplier) and the optimizer places that exact card in a lineup
  2. User can lock a golfer by name and the optimizer includes at least one of their cards across the lineups
  3. User can exclude a card or golfer and no matching card appears in any lineup
  4. When locked cards make optimization infeasible, the app surfaces a specific error (salary over cap, collection limit exceeded) before running the solver
  5. When a lock and exclude target the same card or player, the app warns the user and does not proceed
  6. Uploading new CSVs clears all lock and exclude selections from the previous session
**Plans**: 3 plans

Plans:
- [x] 04-01-PLAN.md — ConstraintSet module and unit test suite (TDD, LOCK-01 through EXCL-02)
- [x] 04-02-PLAN.md — Composite key migration and engine ILP constraint injection (LOCK-01, LOCK-02, EXCL-01, EXCL-02)
- [x] 04-03-PLAN.md — Flask session integration and reset banner (UI-04)

### Phase 5: Serialization and Re-Optimize Route
**Goal**: Users can trigger a fresh optimization using their current lock/exclude selections without re-uploading the roster and projections CSVs
**Depends on**: Phase 4
**Requirements**: UI-02
**Success Criteria** (what must be TRUE):
  1. User can click Re-Optimize on the results page and receive updated lineups reflecting the current lock/exclude state
  2. Re-optimize works without uploading any files — the original card pool is preserved across requests
  3. Results from re-optimize are identical in layout to the original optimize results
**Plans**: 2 plans

Plans:
- [ ] 05-01-PLAN.md — Card serialization helpers and POST /reoptimize route (TDD, UI-02)
- [ ] 05-02-PLAN.md — Re-Optimize form and JS overlay listener in index.html (UI-02)

### Phase 6: Lock/Exclude UI
**Goal**: Users can see their full eligible card pool after uploading CSVs and toggle lock/exclude on individual cards before or after optimizing
**Depends on**: Phase 5
**Requirements**: UI-01, UI-03
**Success Criteria** (what must be TRUE):
  1. After uploading CSVs, user sees a table of all eligible cards with a lock control and an exclude control per row
  2. After optimizing, locked cards in the lineup output are visually distinguished so the user can confirm the constraint took effect
  3. Lock and exclude toggles persist through a re-optimize cycle — selections made before optimizing are still active after results render
**Plans**: TBD

### Phase 7: Polish
**Goal**: Users can manage their lock/exclude state efficiently without having to manually uncheck individual selections
**Depends on**: Phase 6
**Requirements**: UI-05, UI-06
**Success Criteria** (what must be TRUE):
  1. User can clear all active locks and excludes with a single button, resetting the state without re-uploading CSVs
  2. A count of active locks and excludes is visible above the Optimize button so users know their current constraint state at a glance
**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Data Foundation | v1.0 | 4/4 | Complete | 2026-03-13 |
| 2. Optimization Engine | v1.0 | 3/3 | Complete | 2026-03-13 |
| 3. Web Application and Deployment | v1.0 | 3/3 | Complete | 2026-03-13 |
| 4. Constraint Foundation | v1.1 | 3/3 | Complete | 2026-03-14 |
| 5. Serialization and Re-Optimize Route | 2/2 | Complete   | 2026-03-14 | - |
| 6. Lock/Exclude UI | v1.1 | 0/? | Not started | - |
| 7. Polish | v1.1 | 0/? | Not started | - |

---
*Roadmap created: 2026-03-13*
*Last updated: 2026-03-14 after Phase 5 planning (2 plans created)*
