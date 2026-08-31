FROM python:3.12-alpine3.24@sha256:d09d15e60962ca365d1cd544a48773bac9d33f2fb1b00f2aa0deec78ade7dc31

COPY --from=ghcr.io/astral-sh/uv:0.10.7@sha256:edd1fd89f3e5b005814cc8f777610445d7b7e3ed05361f9ddfae67bebfe8456a /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    CSC_HOST=0.0.0.0 \
    CSC_PORT=8103 \
    CSC_DATABASE_PATH=/data/conversation_success_coach.db \
    CSC_DEMO_SEED=true \
    CSC_DOCS_ENABLED=true \
    PATH=/app/.venv/bin:$PATH

WORKDIR /app

RUN apk upgrade --no-cache \
    && addgroup -S -g 10001 coach \
    && adduser -S -D -H -u 10001 -G coach -h /app -s /sbin/nologin coach \
    && mkdir -p /data \
    && chown coach:coach /data

COPY pyproject.toml uv.lock README.md LICENSE NOTICE ./
COPY src ./src

RUN uv sync --locked --no-dev --no-editable \
    && chown -R coach:coach /app

USER coach

EXPOSE 8103
VOLUME ["/data"]

HEALTHCHECK --interval=20s --timeout=3s --start-period=8s --retries=3 \
    CMD ["python", "-c", "import json, urllib.request; data=json.load(urllib.request.urlopen('http://127.0.0.1:8103/api/v1/health', timeout=2)); assert data['status']=='ok'"]

CMD ["uv", "run", "--locked", "--no-dev", "--no-sync", "conversation-success-coach", "serve", "--host", "0.0.0.0", "--port", "8103"]
