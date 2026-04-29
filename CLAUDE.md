# Project Name

## Project

<!-- Description

- **Repo:** https://github.com/NatoJenkins/REPO-NAME-HERE
- **Local:** Windows 11, PowerShell (no `grep` — use `Select-String`)
- **VPS deploy:** `deploy@193.46.198.60:/home/deploy/PROJECT-FOLDER-NAME-HERE/`
-->

## Stack

<!-- e.g. Python 3.11, FastAPI, PostgreSQL 16, SQLAlchemy 2.0, Docker Compose -->

## Phases

<!-- Define your phases here. Example:
- **v1:** Database setup, load data into Postgres, validate schema and data integrity
- **v2:** Feature engineering, model training, walk-forward validation, inference, scheduler
- **v3:** API endpoints (HTTP-only read layer over predictions table)

Stay on phase. Do not build ahead.
-->

## Current State

<!-- Update this section as the project progresses. Include:
- Current phase and what's done
- Alembic revision (local and VPS)
- Test count
- VPS deploy status
-->

**Start every session by reading:**
- `tasks/todo.md` — decisions log and task history
- `tasks/lessons.md` — rules from past corrections (this project)
- `E:\ClaudeCodeProjects\knowledge-base\LESSONS.md` — cross-project rules
- Memory file (auto-loaded from `~/.claude/projects/`)

<!-- FOR SPORTS PREDICTION PROJECTS: Add these lines:
- `../knowledge-base/LESSONS.md` — sports prediction domain rules
- `../knowledge-base/PATTERNS.md` — sports prediction patterns
-->

## Database State

<!-- Table inventory with row counts. Update as migrations land.

| Table | Rows | Notes |
|---|---|---|
-->

## Pipelines

<!-- Pipeline run order and descriptions. Order matters.

| Pipeline | Source | Key Logic |
|---|---|---|
-->

## Key Gotchas

<!-- Capture anything surprising that would trip up a future session.
Format: bold one-liner, then explanation. -->

## Reference Documents

<!-- List the documents that guide this project. Read before planning.

1. **PREDICTION_MODEL_REFERENCE.md** — Architecture patterns, L1+L2 design,
   feature engineering, walk-forward validation.
2. **sports_prediction_api_spec_v2.docx** — API response format. Required
   fields, nullable handling, sport_id/league_id values.
-->

## Workflow

Follow this loop for every non-trivial task:

1. **Research First** — Investigate the current state. Read relevant files, check existing schemas, explore the data. Understand before proposing.
2. **Plan** — Write plan to `tasks/todo.md`. No code until the plan exists.
3. **Verify Plan** — Present the plan for review before executing.
4. **Track Progress** — Mark items complete in todo.md as you go.
5. **Explain Changes** — Summarize what you did at each step.
6. **Document Results** — Add a review section to todo.md when done.
7. **Capture Lessons** — After any correction, write a rule to `tasks/lessons.md` that prevents the same mistake.
8. **Curate Knowledge** — After updating `tasks/lessons.md` or `tasks/todo.md`, run `/curate` to extract generalizable learnings to the knowledge base.

## Commits

Atomic commits only. One logical change per commit. If you're adding an endpoint and notice an unrelated typo, that's two commits.

## Versioning

Single source of truth for the application version is `CHANGELOG.md` at the repo root (Keep a Changelog format). Bump `pyproject.toml`'s `version` field in the same commit as the changelog entry — it mirrors the topmost `## [X.Y.Z]` heading and must never drift. The Flask context processor in `gbgolf/web/__init__.py` reads the version through `gbgolf.changelog.get_latest_version()` and injects it into every template.

## Rules

- **Plan before executing.** Any task with 3+ steps gets a plan first.
- **Investigate, don't guess.** Diagnose actual causes. No "probably" or "likely" explanations. Define investigation steps, run them, report findings.
- **Verify before done.** Never mark a task complete without proving it works. Run the code, check the output, confirm the behavior.
- **Ask before destructive operations.** Deleting data, dropping tables, overwriting files — confirm first.
- **Write and run tests.** Code needs tests. Tests must pass before marking a task complete.
- **Separate builder from evaluator.** The agent that writes the code should not be the same agent that tests or reviews it. Use subagents to enforce separation.
- **Pin every import.** Every `import X` in a source file must have X in `requirements.txt` with an exact version. Docker images build from `requirements.txt` only — transitive dependencies from the host environment will not be there. Verify before committing: check new imports against `requirements.txt` and add any missing entries.
- **Curate after lessons.** After writing to `tasks/lessons.md`, invoke `/curate` to evaluate for knowledge base extraction. Autonomous mode: extract without approval, log all additions.

## VPS Operations

Before any VPS interaction, read `/home/deploy/VPS_STATE.md` for current port allocations, container inventory, and conventions.

After any VPS modification (new ports, containers, volumes, services), update `/home/deploy/VPS_STATE.md` with the changes before ending the session.

**SSH access:** `ssh deploy@193.46.198.60`

**READ-ONLY commands — run freely, no approval needed:**
- `docker ps`, `docker logs`, `docker inspect`, `docker images`, `docker network ls`, `docker volume ls`
- `ls`, `cat`, `head`, `tail`, `df`, `pwd`, `whoami`, `hostname`, `dmesg`, `journalctl`
- Any command that only reads state

**MODIFICATION commands — tell me what you're about to run and WAIT for approval:**
- `docker compose up/down/restart/stop/start`, `docker stop/start/rm`
- `mkdir`, `cp`, `mv`, `rm`, `touch`, `chmod`, `chown`
- `git clone`, `git pull`, `git checkout`
- Any edits to files on VPS
- Any command that writes to filesystem or changes container state

### Approval Cadence

**One approval = one modifying command. This is the default.** Do not batch-execute multiple modifications under a single approval.

- After describing a modifying command, **STOP and wait** for explicit "proceed", "approved", or equivalent before executing.
- Only batch-execute if the user explicitly specifies a range, e.g. "execute steps 1-5", "proceed with items 2 through 4", or "run all pipeline commands". Without explicit batch authorization, assume one-at-a-time.
- Read-only commands do not require approval and can run freely between modification steps.
- A previous "approved" does NOT carry forward to the next modifying command. Each one needs its own greenlight unless the user explicitly said otherwise.

**Examples:**

| User says | Claude does |
|---|---|
| "VPS deployment approved" | Run Step 1 (read-only checks). Describe Step 2. **STOP. Wait.** |
| "proceed" | Run Step 2. Describe Step 3. **STOP. Wait.** |
| "proceed with steps 3-6" | Run steps 3, 4, 5, 6 in sequence. Describe Step 7. **STOP. Wait.** |
| "go ahead and run the whole sequence" | Run all remaining modification steps in order. Stop only on error. |
| "approved" (no scope qualifier) | Run only the most recently described command. **STOP. Wait.** |

**If in doubt, default to one-at-a-time.** Asking again is cheap; unwinding a wrong batch operation is not.

## Knowledge Base

This project contributes to and reads from the shared knowledge base system:

| Tier | Location | Contents |
|---|---|---|
| Global | `E:\ClaudeCodeProjects\knowledge-base\` | Cross-project patterns, deployment, stack |
| Domain | `E:\ClaudeCodeProjects\Sports-Prediction-API\knowledge-base\` | Sports prediction specific (if applicable) |
| Project | `tasks/lessons.md` | This project only |

**Commands:**
- `/curate` — Extract generalizable learnings (run after lessons.md updates)
- `/extract-final` — End-of-project comprehensive extraction
