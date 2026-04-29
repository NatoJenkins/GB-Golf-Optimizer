# Backlog: deploy.sh does not install Python dependencies

## Context

`deploy/deploy.sh` syncs files, runs `flask db upgrade`, and restarts the gunicorn service. It does **not** install Python dependencies. Any new entry added to `pyproject.toml`'s `dependencies` array reaches production code but not the production venv, causing a `ModuleNotFoundError` at the first request that imports the new package.

This bit us during the v1.2.2 deploy: `markdown>=3.5` was added to `pyproject.toml` for the changelog page, deploy ran cleanly, but `/changelog` 500'd in production. Manual fix:

```
ssh deploy@193.46.198.60 "/opt/GBGolfOptimizer/.venv/bin/pip install 'markdown>=3.5' && sudo systemctl restart gbgolf"
```

## Fix

Add a dependency-install step to `deploy/deploy.sh` between the tar sync and `db upgrade`. Recommended:

```bash
echo "Installing dependencies..."
ssh "$REMOTE" "cd $REMOTE_PATH && .venv/bin/pip install -e . --quiet"
```

This installs the project (and its `dependencies` array from `pyproject.toml`) into the venv editably. `--quiet` keeps output clean unless something fails. Idempotent: re-running with no new deps is a fast no-op.

Alternative if `-e .` is undesirable: pin the install to non-editable `.venv/bin/pip install . --quiet`.

## Risk to consider when implementing

- A failing pip install would currently leave the previous code installed but with new dependencies missing. Order of ops in the script matters: `set -e` already aborts on failure, so a failed install would skip the migration and restart. The previous service stays running on old code — safe default. Verify before shipping.
- Adding this step adds latency to every deploy (typically 2-5s for a no-op). Acceptable.
- If anyone manually pip-installs into the prod venv (as we just did with markdown), running `pip install -e .` afterward is harmless — pip detects already-satisfied requirements.

## Verification when implemented

1. Add a deliberately-bogus extra dep to `pyproject.toml` on a test branch
2. Run `bash deploy/deploy.sh` — should fail at the install step, NOT at request time
3. Revert and confirm normal deploys still work
