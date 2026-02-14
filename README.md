# dotview

Lightweight read-only file browser for git repos with syntax highlighting. Clone any repo, pull on a schedule, and serve a browsable tree view.

## Features

- Directory tree navigation with breadcrumbs
- Syntax highlighting via [highlight.js](https://highlightjs.org/) (Catppuccin Mocha theme)
- Styled with [Pico CSS](https://picocss.com/)
- Auto-pulls from remote on a configurable interval
- Supports private repos via token auth

## Configuration

All config is via environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DOTVIEW_REPO_URL` | Yes | — | Git repo URL to clone |
| `DOTVIEW_GIT_TOKEN` | No | — | GitHub PAT for private repos |
| `DOTVIEW_BRANCH` | No | `main` | Branch to track |
| `DOTVIEW_PULL_INTERVAL` | No | `300` | Seconds between pulls |
| `DOTVIEW_REPO_DIR` | No | `/data/repo` | Where to clone the repo |

## Docker

```bash
docker run -d \
  -p 8080:8080 \
  -e DOTVIEW_REPO_URL=https://github.com/user/repo \
  -e DOTVIEW_BRANCH=main \
  -v dotview-data:/data \
  ghcr.io/noahkiss/dotview:main
```

For private repos, add `-e DOTVIEW_GIT_TOKEN=ghp_...`.

## Docker Compose

```yaml
services:
  dotview:
    image: ghcr.io/noahkiss/dotview:main
    ports:
      - "8080:8080"
    environment:
      DOTVIEW_REPO_URL: "https://github.com/user/repo"
      DOTVIEW_BRANCH: "main"
      DOTVIEW_PULL_INTERVAL: "300"
    volumes:
      - dotview-data:/data

volumes:
  dotview-data:
```

## Local development

```bash
uv sync
DOTVIEW_REPO_DIR=. uv run flask --app app run --port 8080
```

This serves the dotview project itself as a demo.
