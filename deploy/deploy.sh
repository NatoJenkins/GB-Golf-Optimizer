#!/usr/bin/env bash
# Deploy GB Golf Optimizer to VPS
# Usage: bash deploy/deploy.sh
set -e

REMOTE="deploy@193.46.198.60"
REMOTE_PATH="/opt/GBGolfOptimizer"
LOCAL_PATH="$(cd "$(dirname "$0")/.." && pwd)"

echo "Syncing files..."
tar -czf - \
  --exclude='./.planning' \
  --exclude='./.git' \
  --exclude='./__pycache__' \
  --exclude='./**/__pycache__' \
  --exclude='./*.pyc' \
  --exclude='./**/*.pyc' \
  --exclude='./venv' \
  --exclude='./.venv' \
  --exclude='./*.sock' \
  -C "$LOCAL_PATH" . \
  | ssh "$REMOTE" "tar -xzf - -C $REMOTE_PATH"

echo "Running database migration..."
ssh "$REMOTE" "cd $REMOTE_PATH && FLASK_APP=gbgolf.web:create_app .venv/bin/flask db upgrade"

echo "Restarting service..."
ssh "$REMOTE" "sudo systemctl restart gbgolf && systemctl status gbgolf --no-pager"

echo "Done. Visit https://gameblazers.silverreyes.net/golf"
