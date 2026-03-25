#!/usr/bin/env bash
# Deploy GB Golf Optimizer to VPS
# Usage: bash deploy/deploy.sh

set -e

REMOTE="deploy@193.46.198.60"
REMOTE_PATH="/opt/GBGolfOptimizer"
LOCAL_PATH="$(cd "$(dirname "$0")/.." && pwd)"

echo "Syncing files..."
rsync -rlvz --checksum --delete \
  --exclude='.planning' \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.pyc' \
  --exclude='venv' \
  --exclude='*.sock' \
  "$LOCAL_PATH/" "$REMOTE:$REMOTE_PATH/"

echo "Restarting service..."
ssh "$REMOTE" "systemctl restart gbgolf && systemctl status gbgolf --no-pager"

echo "Done. Visit http://gameblazers.silverreyes.net/golf"
