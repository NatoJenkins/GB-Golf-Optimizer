---
status: complete
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
result: pass

### 3. Clear All Resets Constraint Count
expected: With some locks/excludes active (constraint count showing), click the "Clear All" button. All checkboxes clear and the constraint count display disappears (returns to hidden/empty state).
result: pass

### 4. Sortable Player Pool Table — Click Column Header to Sort
expected: After running an optimization, click any column header in the player pool table (e.g. "Salary", "Proj", "Owned"). The table rows re-sort by that column — descending on first click. No page reload occurs; the re-sort is instant in-browser.
result: pass

### 5. Sort Indicator Shown on Active Column
expected: When a column is sorted, that column's header shows a ▲ or ▼ indicator. Clicking the same header again reverses the sort direction and flips the indicator. Other column headers have no indicator.
result: pass

### 6. Default Sort Indicator on Page Load
expected: When results first appear (after POST), the Player column header shows a ▲ indicator by default (matching the server's A-Z sort order), with no indicators on other columns.
result: pass

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0
skipped: 0

## Gaps

[none — all issues resolved]
