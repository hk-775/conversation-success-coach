FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CSC_HOST=0.0.0.0 \
    CSC_PORT=8103 \
    CSC_DATABASE_PATH=/data/conversation_success_coach.db \
    CSC_DEMO_SEED=true \
    CSC_DOCS_ENABLED=true

WORKDIR /app

RUN addgroup --system coach \
    && adduser --system --ingroup coach --home /nonexistent coach \
    && mkdir -p /data \
    && chown coach:coach /data

COPY pyproject.toml README.md LICENSE NOTICE ./
COPY src ./src

RUN python -m pip install --no-cache-dir .

USER coach

EXPOSE 8103
VOLUME ["/data"]

HEALTHCHECK --interval=20s --timeout=3s --start-period=8s --retries=3 \
    CMD ["python", "-c", "import json, urllib.request; data=json.load(urllib.request.urlopen('http://127.0.0.1:8103/api/v1/health', timeout=2)); assert data['status']=='ok'"]

CMD ["conversation-success-coach", "serve", "--host", "0.0.0.0", "--port", "8103"]

