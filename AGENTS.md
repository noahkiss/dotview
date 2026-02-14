# dotview

Lightweight read-only file browser for Git repos with syntax highlighting. Runs as a Docker container that clones a repo and serves it via Flask.

## Architecture

Single-file Flask app (`app.py`) with Jinja2 templates. No database, no auth — intentionally minimal.

- `app.py` — Flask app, all routes and logic
- `templates/` — Jinja2 templates (tree view, file view)
- `entrypoint.sh` — Clones/pulls repo, starts gunicorn
- `Dockerfile` — Production image using uv for dependency management

## Local Dev

```bash
# Install dependencies
uv sync

# Run locally (point at any git repo)
DOTVIEW_REPO_DIR=. uv run gunicorn --bind 0.0.0.0:8080 app:app

# Or use Flask dev server for auto-reload
DOTVIEW_REPO_DIR=. uv run flask --app app run --port 8080 --debug
```

## Docker

```bash
docker build -t dotview .
docker run -e DOTVIEW_REPO_URL=https://github.com/user/repo dotview
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DOTVIEW_REPO_URL` | Yes (Docker) | — | Git URL to clone |
| `DOTVIEW_REPO_DIR` | No | `/data/repo` | Path to repo on disk |
| `DOTVIEW_BRANCH` | No | `main` | Branch to track |
| `DOTVIEW_PULL_INTERVAL` | No | `300` | Seconds between background pulls |
| `DOTVIEW_GIT_TOKEN` | No | — | Token for private repo auth |

## Stack

- Python 3.13, Flask, gunicorn
- highlight.js (CDN) for syntax highlighting
- uv for dependency management
