FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir flask

COPY app.py entrypoint.sh ./
COPY templates/ templates/

RUN mkdir -p /data/repo

EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
