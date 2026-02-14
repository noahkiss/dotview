FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-editable

COPY app.py entrypoint.sh ./
COPY templates/ templates/

RUN mkdir -p /data/repo

EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
