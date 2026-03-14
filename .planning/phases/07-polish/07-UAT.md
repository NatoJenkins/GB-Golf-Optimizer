---
status: diagnosed
phase: 07-polish
source: 07-01-SUMMARY.md, 07-02-SUMMARY.md
started: 2026-03-14T20:30:00Z
updated: 2026-03-14T20:30:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Constraint Count Hidden When No Constraints Active
expected: After running an optimization (POST with results showing), with no locks or excludes checked, the constraint count area shows nothing (is hidden/empty — not displaying "Locks: 0 | Excludes: 0").
result: pass

### 2. Constraint Count Shows Active Locks and Excludes
expected: Check one or more Lock checkboxes and/or one or more Exclude checkboxes in the player pool. The constraint count display updates immediately to show "Locks: N | Excludes: N" (e.g. "Locks: 1 | Excludes: 2") reflecting the current counts.
result: issue
reported: "checked three different boxes for three different golfers (Justin Rose Lock, Adam Scott Lock Golfer, Lee Hodges Exclude) on results page — nothing changes or appears"
severity: major

### 3. Clear All Resets Constraint Count
expected: With some locks/excludes active (constraint count showing), click the "Clear All" button. All checkboxes clear and the constraint count display disappears (returns to hidden/empty state).
result: skipped
reason: Depends on test 2 (constraint count display) which failed

### 4. Sortable Player Pool Table — Click Column Header to Sort
expected: After running an optimization, click any column header in the player pool table (e.g. "Salary", "Proj", "Owned"). The table rows re-sort by that column — descending on first click. No page reload occurs; the re-sort is instant in-browser.
result: issue
reported: "None of the headers on the player list are clickable or sortable"
severity: major

### 5. Sort Indicator Shown on Active Column
expected: When a column is sorted, that column's header shows a ▲ or ▼ indicator. Clicking the same header again reverses the sort direction and flips the indicator. Other column headers have no indicator.
result: skipped
reason: Depends on test 4 (sort functionality) which failed

### 6. Default Sort Indicator on Page Load
expected: When results first appear (after POST), the Player column header shows a ▲ indicator by default (matching the server's A-Z sort order), with no indicators on other columns.
result: issue
reported: "There are no indicators on any of the column headers"
severity: major

## Summary

total: 6
passed: 1
issues: 3
pending: 0
skipped: 2
skipped: 0

## Gaps

- truth: "Constraint count display shows 'Locks: N | Excludes: N' when checkboxes are active on results page"
  status: failed
  reason: "User reported: checked three different boxes for three different golfers (Justin Rose Lock, Adam Scott Lock Golfer, Lee Hodges Exclude) on results page — nothing changes or appears"
  severity: major
  test: 2
  root_cause: "<details id='player-pool-section'> renders collapsed by default — checkboxes are in the DOM but hidden, so updateConstraintCount() is never triggered"
  artifacts:
    - path: "gbgolf/web/templates/index.html"
      issue: "Missing 'open' attribute on <details id='player-pool-section'> at line 59"
  missing:
    - "Add open attribute: <details id='player-pool-section' open>"

- truth: "Player pool column headers are clickable and sort the table in-browser on first click (descending)"
  status: failed
  reason: "User reported: None of the headers on the player list are clickable or sortable"
  severity: major
  test: 4
  root_cause: "<details id='player-pool-section'> renders collapsed — th elements with onclick handlers exist in DOM but are invisible to the user"
  artifacts:
    - path: "gbgolf/web/templates/index.html"
      issue: "Missing 'open' attribute on <details id='player-pool-section'> at line 59"
  missing:
    - "Add open attribute: <details id='player-pool-section' open>"

- truth: "Player column header shows ▲ indicator by default on page load after optimization"
  status: failed
  reason: "User reported: There are no indicators on any of the column headers"
  severity: major
  test: 6
  root_cause: "updateSortIndicators(3, true) runs correctly at page load and writes ▲ to the DOM, but <details> is collapsed so it's hidden"
  artifacts:
    - path: "gbgolf/web/templates/index.html"
      issue: "Missing 'open' attribute on <details id='player-pool-section'> at line 59"
  missing:
    - "Add open attribute: <details id='player-pool-section' open>"
