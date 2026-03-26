# Requirements: GB Golf Optimizer

**Defined:** 2026-03-14
**Core Value:** Generate the best possible cash contest lineups from the user's available player cards, maximizing expected score within salary and collection constraints.

## v1.2 Requirements

Requirements for the Automated Projection Fetching milestone.

### Data Fetching & Storage (FETCH)

- [x] **FETCH-01**: System fetches player projections from the DataGolf `fantasy-projection-defaults` API (PGA Tour, DraftKings scoring, main slate) and writes them to a PostgreSQL database
- [x] **FETCH-02**: A cron job on the VPS triggers the fetcher automatically on Tuesday and Wednesday mornings
- [x] **FETCH-03**: Fetch activity (player count, tournament name, timestamp, any errors) is written to a log file on the VPS
- [x] **FETCH-04**: Existing stored projections are preserved if the API returns an error or fewer than a minimum viable player count
- [x] **FETCH-05**: Fetched projections are stored with player name, projected score, tournament name, and fetch timestamp per record
- [x] **FETCH-06**: DataGolf player names ("Last, First" format) are normalized to "First Last" before storage to match GameBlazers roster names

### Projection Source (SRC)

- [x] **SRC-01**: User can select "DataGolf" or "Upload CSV" as the projection source before running the optimizer
- [x] **SRC-02**: When "DataGolf" is selected, the optimizer uses the most recently stored projections from the database
- [x] **SRC-03**: When "DataGolf" is selected and projections exist, the UI displays the stored tournament name and relative fetch age (e.g., "Arnold Palmer Invitational — fetched 8 days ago"), regardless of whether the data is from the current week or a prior week
- [x] **SRC-04**: If no projections have ever been fetched (database is empty), the DataGolf option is disabled with a "No projections available yet" message; stale prior-week projections are never hidden
- [x] **SRC-05**: When "DataGolf" is selected, unmatched player warnings are shown for roster players whose projections are not in the database (extends existing unmatched player report)

## v1.1 Requirements (Completed: 2026-03-25)

### Lock Controls

- [x] **LOCK-01**: User can lock a specific card (identified by player + multiplier) to force it into the optimizer
- [x] **LOCK-02**: User can lock a golfer by name to force at least one of their cards into a lineup
- [x] **LOCK-03**: App shows an informative error when locked cards make salary or collection constraints infeasible before running the optimizer
- [x] **LOCK-04**: App warns user when a lock and exclude conflict on the same player or card

### Exclude Controls

- [x] **EXCL-01**: User can exclude a specific card from all lineups in this session
- [x] **EXCL-02**: User can exclude a golfer by name, removing all their cards from all lineups

### UI Surface

- [x] **UI-01**: User sees their eligible player pool with per-card lock/exclude controls after uploading CSVs
- [x] **UI-02**: User can re-optimize with updated lock/exclude selections without re-uploading CSVs
- [x] **UI-03**: Locked cards are visually marked in lineup output confirming constraints took effect
- [x] **UI-04**: Lock/exclude state resets automatically when new CSVs are uploaded
- [x] **UI-05**: User can clear all locks and excludes with a single button
- [x] **UI-06**: App shows count of active locks and excludes above the Optimize button

## Future Requirements

Deferred to future releases. Tracked but not in current roadmap.

### Advanced Optimizer

- **ADV-01**: User can set exposure limits — cap how often a single golfer appears across all lineups
- **ADV-02**: User can enforce diversity constraints — minimum player differences between lineups
- **ADV-03**: User can run sensitivity analysis — see how a lineup changes if a player's projection shifts

### UI Polish

- **USBL-01**: User can edit contest configuration in the web UI
- **USBL-02**: User can view card comparison — side-by-side display of multiple cards for same player
- **USBL-04**: User can export lineups — copy to clipboard or download as CSV

### Projection Management (post-v1.2)

- **MGMT-01**: User can trigger a manual projection refresh from the UI without waiting for the cron schedule
- **MGMT-02**: UI shows a fetch status dashboard with last fetch time, player count, and error history

### Advanced Sources (v2.0)

- **MSRC-01**: User can upload a custom CSV and compare projected scores side-by-side with DataGolf projections before optimizing
- **MSRC-02**: System supports averaging projections across multiple sources with configurable weights

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multi-source projection averaging | Single DataGolf source for v1.2; averaging across sources is v2.0 |
| DataGolf data beyond projections | v1.2 uses `fantasy-projection-defaults` only — no strokes gained, rankings, or historical data |
| Fuzzy player name matching | Golf has too many similar names; explicit alias table populated from live testing is correct approach |
| User accounts / per-user projection storage | v1.3 — schema designed for extensibility but not implemented here |
| DataGolf salary data (DraftKings) | GameBlazers has its own salary system; DK salary from DataGolf is irrelevant |
| Projection history / snapshots | Only latest projections per event retained; no historical projection archive |
| Per-lineup lock assignment | No major DFS tool offers it; cross-contest card locking forces lineup diversity naturally |
| Persistent lock/exclude (week to week) | Session-scoped is sufficient; reset-on-upload confirmed acceptable |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FETCH-01 | Phase 9 | Complete |
| FETCH-02 | Phase 9 | Complete |
| FETCH-03 | Phase 9 | Complete |
| FETCH-04 | Phase 9 | Complete |
| FETCH-05 | Phase 8 | Complete |
| FETCH-06 | Phase 9 | Complete |
| SRC-01 | Phase 10 | Complete |
| SRC-02 | Phase 10 | Complete |
| SRC-03 | Phase 10 | Complete |
| SRC-04 | Phase 10 | Complete |
| SRC-05 | Phase 10 | Complete |

**Coverage:**
- v1.2 requirements: 11 total
- Mapped to phases: 11
- Unmapped: 0
- Phase 11 (Deploy and Verification): verification phase — validates all requirements in production, owns no unique requirements

---
*Requirements defined: 2026-03-14*
*Last updated: 2026-03-25 after v1.2 roadmap creation (traceability populated)*
