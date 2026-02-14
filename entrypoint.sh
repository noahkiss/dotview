#!/bin/sh
set -e

REPO_URL="${DOTVIEW_REPO_URL:?DOTVIEW_REPO_URL is required}"
REPO_DIR="${DOTVIEW_REPO_DIR:-/data/repo}"
BRANCH="${DOTVIEW_BRANCH:-main}"
PULL_INTERVAL="${DOTVIEW_PULL_INTERVAL:-300}"

log() {
  echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] $*"
}

# Set up git auth if token provided
if [ -n "$DOTVIEW_GIT_TOKEN" ]; then
  # Works for GitHub: https://<token>@github.com/user/repo
  AUTHED_URL=$(echo "$REPO_URL" | sed "s|https://|https://${DOTVIEW_GIT_TOKEN}@|")
else
  AUTHED_URL="$REPO_URL"
fi

# Initial clone or pull
if [ ! -d "$REPO_DIR/.git" ]; then
  log "Cloning $REPO_URL (branch: $BRANCH)..."
  git clone --branch "$BRANCH" --single-branch "$AUTHED_URL" "$REPO_DIR"
  log "Clone complete."
else
  log "Repo exists, pulling latest..."
  cd "$REPO_DIR"
  if git pull origin "$BRANCH"; then
    log "Pull complete."
  else
    log "ERROR: Pull failed, continuing with existing data" >&2
  fi
fi

# Background pull loop
(
  while true; do
    sleep "$PULL_INTERVAL"
    cd "$REPO_DIR"
    if ! git pull origin "$BRANCH" 2>&1 | grep -qv "Already up to date"; then
      true  # suppress "Already up to date" noise
    fi
  done
) &

# Start the server
cd /app
exec .venv/bin/gunicorn --bind 0.0.0.0:8080 app:app
