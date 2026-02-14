#!/bin/sh
set -e

REPO_URL="${DOTVIEW_REPO_URL:?DOTVIEW_REPO_URL is required}"
REPO_DIR="${DOTVIEW_REPO_DIR:-/data/repo}"
BRANCH="${DOTVIEW_BRANCH:-main}"
PULL_INTERVAL="${DOTVIEW_PULL_INTERVAL:-300}"

# Set up git auth if token provided
if [ -n "$DOTVIEW_GIT_TOKEN" ]; then
  # Works for GitHub: https://<token>@github.com/user/repo
  AUTHED_URL=$(echo "$REPO_URL" | sed "s|https://|https://${DOTVIEW_GIT_TOKEN}@|")
else
  AUTHED_URL="$REPO_URL"
fi

# Initial clone or pull
if [ ! -d "$REPO_DIR/.git" ]; then
  echo "Cloning $REPO_URL (branch: $BRANCH)..."
  git clone --branch "$BRANCH" --single-branch "$AUTHED_URL" "$REPO_DIR"
else
  echo "Repo exists, pulling latest..."
  cd "$REPO_DIR"
  git pull origin "$BRANCH" || echo "Pull failed, continuing with existing data"
fi

# Background pull loop
(
  while true; do
    sleep "$PULL_INTERVAL"
    cd "$REPO_DIR"
    git pull origin "$BRANCH" 2>&1 | grep -v "Already up to date" || true
  done
) &

# Start the server
cd /app
exec flask --app app run --host 0.0.0.0 --port 8080
