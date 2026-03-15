---
status: resolved
trigger: "lock column shows no icon when golfer is locked by name"
created: 2026-03-14T00:00:00Z
updated: 2026-03-14T00:01:00Z
---

## Current Focus

hypothesis: The lineup result table checks only `locked_card_keys` for the lock icon, never `locked_golfer_set`. A name-locked golfer's card will not match a card-key lookup, so no icon appears.
test: Confirmed by reading template line 162 and route reoptimize return at line 215-225.
expecting: Fix is to also check `locked_golfer_set` (card.player in locked_golfer_set) in the lock column cell of the results table.
next_action: Await human verification of fix

## Symptoms

expected: When a golfer is locked by name, the lock icon appears in the lock column of the optimized lineup for that player.
actual: The lock icon does not appear in the optimized lineup when the lock was set by golfer name. The player may still be included, but the lock column shows no icon.
errors: No crash — purely a display/data issue.
reproduction: 1) Lock a golfer by their name, 2) Run optimization, 3) View optimized lineups — first (lock) column is empty for that player even if they appear.
timeline: Unknown — likely always been this way. Card-locking works correctly.

## Eliminated

- hypothesis: `locked_golfer_set` is not passed to the template
  evidence: `reoptimize` route (routes.py line 225) passes `locked_golfer_set=set(locked_golfers)` to render_template. It IS available in the template.
  timestamp: 2026-03-14

- hypothesis: The optimizer fails to include name-locked players
  evidence: engine.py lines 79-83 add an ILP constraint forcing at least one card per locked golfer. The player is included; only the icon is missing.
  timestamp: 2026-03-14

## Evidence

- timestamp: 2026-03-14
  checked: templates/index.html line 162 (lock icon cell in results table)
  found: `{% if locked_card_keys and (card.player, card.salary, card.multiplier, card.collection) in locked_card_keys %}🔒{% endif %}`
  implication: Icon only fires on exact card-key match. Name-locked players are never matched here because their lock is stored in `locked_golfer_set`, not `locked_card_keys`.

- timestamp: 2026-03-14
  checked: routes.py reoptimize() return (lines 215-225)
  found: Both `locked_card_keys=set(locked_cards)` and `locked_golfer_set=set(locked_golfers)` are passed to the template.
  implication: `locked_golfer_set` is available in the template context — it just isn't used in the results table lock-icon condition.

- timestamp: 2026-03-14
  checked: routes.py index() return (lines 112-123) — fresh file upload path
  found: `locked_card_keys=set()` and `locked_golfer_set=set()` (both empty) — correct, since locks are cleared on new upload.
  implication: No issue on the upload path; bug is only in the reoptimize path.

## Resolution

root_cause: The lock-icon condition in the optimized lineups table (index.html line 162) only checks `locked_card_keys`. It does not check `locked_golfer_set`. When a golfer is locked by name, their card key is not in `locked_card_keys`, so the icon is suppressed even though `locked_golfer_set` contains the player name and the player appears in the lineup.

fix: Extended the Jinja2 condition on line 162 of index.html. The original condition checked only `locked_card_keys`. The new condition is an OR: show the lock icon if the card's composite key is in `locked_card_keys` OR if the card's player name is in `locked_golfer_set`.

verification: Confirmed working on live site by user (2026-03-14).
files_changed:
  - gbgolf/web/templates/index.html
