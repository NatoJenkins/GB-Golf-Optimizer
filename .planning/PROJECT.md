# GB Golf Optimizer

## What This Is

A web application for optimizing GameBlazers fantasy golf lineups. Users upload their weekly roster export (CSV from GameBlazers) and a projections CSV, and the app generates optimal lineups for each available contest — prioritizing the cash contest (The Tips) first, then using remaining cards for The Intermediate Tee. Deployed live at http://gameblazers.silverreyes.net/golf/.

## Core Value

Generate the best possible cash contest lineups from the user's available player cards, maximizing expected score within salary and collection constraints.

## Requirements

### Validated

- ✓ User can upload a GameBlazers roster CSV export — v1.0
- ✓ User can upload a weekly projections CSV (player name + projected score) — v1.0
- ✓ App generates 3 optimal lineups for The Tips (6 golfers, salary $30K–$64K, collection limits) — v1.0
- ✓ App generates 2 optimal lineups for The Intermediate Tee (5 golfers, salary $20K–$52K) using cards not assigned to Tips — v1.0
- ✓ Each card locked to one lineup across all contests — v1.0
- ✓ Optimizer respects both salary floor and cap per contest — v1.0
- ✓ Optimizer respects collection constraints (Weekly/Core limits) per contest — v1.0
- ✓ Effective card value calculated as projected_score × multiplier — v1.0
- ✓ Lineups displayed in browser with player, salary, multiplier, projected value, and totals — v1.0
- ✓ Contest configuration stored in editable JSON file — v1.0
- ✓ Cards with $0 salary excluded from optimization — v1.0
- ✓ Cards past their Expires date excluded from optimization — v1.0
- ✓ Unmatched player report surfaced in UI — v1.0
- ✓ App deployed to Hostinger KVM 2 VPS at gameblazers.silverreyes.net/golf — v1.0

### Active

- [ ] Contest configuration editor in the web UI (USBL-01)
- [ ] Card comparison view — side-by-side display of multiple cards for same player (USBL-02)
- [ ] Manual lock/exclude — user can force a specific card in or out before optimizing (USBL-03)
- [ ] Lineup export — copy to clipboard or download as CSV (USBL-04)
- [ ] Exposure limits — cap how often a single golfer appears across all lineups (ADV-01)
- [ ] Diversity constraints — enforce minimum player differences between lineups (ADV-02)
- [ ] Sensitivity analysis — show how lineup changes if a player's projection shifts (ADV-03)

### Out of Scope

- Scraping GameBlazers for contest data — manual config file update instead (contests change infrequently)
- Automatic projection fetching — user manually averages projections from multiple DFS sites
- User accounts / authentication — single shared app, no login required
- Mobile-native app — web app accessible from any browser
- RUC (Recycling Useless Cards) optimization — separate system
- Stacking constraints — team-sport DFS concept; irrelevant for individual-sport golf
- Overall score in optimization — GameBlazers "Overall" is for RUC card burning only

## Context

- **GameBlazers** (gameblazers.com): fantasy golf platform where users collect player cards with salaries and multipliers (1.0–1.5). Each week, users enter contests by building lineups from their card collection.
- **Roster export**: CSV with columns: Player, Positions, Team, Multiplier, Overall, Franchise, Rookie, Tradeable, Salary, Collection, Status, Expires.
- **Franchise / Rookie columns**: Boolean flags only — not collection types, no optimizer constraints needed. (Confirmed v1.0)
- **Salary $0 cards**: Indicate player not in tournament field this week — excluded from optimization.
- **Duplicate player cards**: Same player can appear multiple times with different multipliers/salaries; each card is a distinct optimizer variable, but a golfer may only appear once per lineup.
- **Two contests**: The Tips (cash, 3 entries) and The Intermediate Tee (non-cash, 2 entries).
- **Scoring**: Eagles (+8), birdies (+4), pars (-0.5), bogeys (-1), double bogeys (-3), double eagle or better (+15), birdie streaks (+3), bogey-free round (+2), hole-in-one (+5), plus finish position bonuses.
- **Projections**: User averages from multiple DFS sites (DataGolf, FantasyNational, etc.) and uploads weekly.
- **Hosting**: Hostinger KVM 2 VPS — full Linux server. Live at gameblazers.silverreyes.net/golf.
- **v1.0 shipped**: 2026-03-13. 1,407 LOC Python. 33 tests, all GREEN. App browser-verified.

## Constraints

- **Tech Stack**: Python (Flask, PuLP, Pydantic v2) + Jinja2/HTML/CSS
- **Hosting**: Hostinger KVM 2 VPS at silverreyes.net — Gunicorn + Nginx + systemd
- **Data input**: No scraping — file uploads (roster CSV, projections CSV) or manual config
- **Card locking**: Each card may only appear in exactly one lineup across all contests in a session

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Manual projections upload (CSV) | Simpler than scraping; user averages multiple sources themselves | ✓ Good |
| Contest config as editable JSON file | Contests change infrequently; scraping is fragile | ✓ Good |
| Python + PuLP for optimization | ILP handles salary/collection/uniqueness constraints cleanly; pure Python | ✓ Good |
| Cash contest optimized first | Maximize prize money; non-cash lineups use leftover cards | ✓ Good |
| Cards locked per lineup (cross-contest) | GameBlazers rule — same card cannot appear in multiple lineup entries | ✓ Good |
| One golfer per lineup | GameBlazers rule — same golfer may only appear once per lineup regardless of cards owned | ✓ Good |
| Franchise/Rookie are flags only | Confirmed with user — not collection types, no ILP constraints needed | ✓ Good |
| Pydantic at boundary only | Validate external JSON with Pydantic, return plain dataclass — avoids coupling in optimizer | ✓ Good |
| Collection limits as upper bounds only | 0 Weekly Collection cards per lineup is legal — constraints are maximums, not minimums | ✓ Good |
| Windows-safe temp file pattern | Write inside with-block, pass path after close — avoids NamedTemporaryFile locking on Windows | ✓ Good |
| SCRIPT_NAME via systemd env var | Flask/Werkzeug reads it to generate correct URLs under /golf prefix without code changes | ✓ Good |
| ProxyFix skipped in TESTING mode | Avoids Flask test client URL generation conflicts | ✓ Good |

---
*Last updated: 2026-03-14 after v1.0 milestone*
