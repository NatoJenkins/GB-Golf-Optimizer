# Requirements: GB Golf Optimizer

**Defined:** 2026-03-14
**Core Value:** Generate the best possible cash contest lineups from the user's available player cards, maximizing expected score within salary and collection constraints.

## v1.1 Requirements

Requirements for the Manual Lock/Exclude milestone.

### Lock Controls

- [ ] **LOCK-01**: User can lock a specific card (identified by player + multiplier) to force it into the optimizer
- [ ] **LOCK-02**: User can lock a golfer by name to force at least one of their cards into a lineup
- [ ] **LOCK-03**: App shows an informative error when locked cards make salary or collection constraints infeasible before running the optimizer
- [ ] **LOCK-04**: App warns user when a lock and exclude conflict on the same player or card

### Exclude Controls

- [ ] **EXCL-01**: User can exclude a specific card from all lineups in this session
- [ ] **EXCL-02**: User can exclude a golfer by name, removing all their cards from all lineups

### UI Surface

- [ ] **UI-01**: User sees their eligible player pool with per-card lock/exclude controls after uploading CSVs
- [ ] **UI-02**: User can re-optimize with updated lock/exclude selections without re-uploading CSVs
- [ ] **UI-03**: Locked cards are visually marked in lineup output confirming constraints took effect
- [ ] **UI-04**: Lock/exclude state resets automatically when new CSVs are uploaded
- [ ] **UI-05**: User can clear all locks and excludes with a single button
- [ ] **UI-06**: App shows count of active locks and excludes above the Optimize button

## v1.2 Requirements

Deferred to future release.

### Advanced Optimizer

- **ADV-01**: User can set exposure limits — cap how often a single golfer appears across all lineups
- **ADV-02**: User can enforce diversity constraints — minimum player differences between lineups
- **ADV-03**: User can run sensitivity analysis — see how a lineup changes if a player's projection shifts

### UI Polish

- **USBL-01**: User can edit contest configuration in the web UI
- **USBL-02**: User can view card comparison — side-by-side display of multiple cards for same player
- **USBL-04**: User can export lineups — copy to clipboard or download as CSV

## Out of Scope

| Feature | Reason |
|---------|--------|
| Per-lineup lock assignment | No major DFS tool offers it; cross-contest card locking already forces lineup diversity naturally |
| Persistent lock/exclude (week to week) | Session-scoped is sufficient; user confirmed reset-on-upload is acceptable |
| Lock/exclude state stored in Flask-Session (server-side) | Cookie session fits comfortably within 4KB limit; no new dependencies needed |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| LOCK-01 | — | Pending |
| LOCK-02 | — | Pending |
| LOCK-03 | — | Pending |
| LOCK-04 | — | Pending |
| EXCL-01 | — | Pending |
| EXCL-02 | — | Pending |
| UI-01 | — | Pending |
| UI-02 | — | Pending |
| UI-03 | — | Pending |
| UI-04 | — | Pending |
| UI-05 | — | Pending |
| UI-06 | — | Pending |

**Coverage:**
- v1.1 requirements: 12 total
- Mapped to phases: 0
- Unmapped: 12 ⚠️

---
*Requirements defined: 2026-03-14*
*Last updated: 2026-03-14 after initial definition*
