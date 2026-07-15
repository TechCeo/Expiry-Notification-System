FROM python:3.13-slim AS builder

ARG PIP_TRUSTED_HOST=""
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST}

WORKDIR /build
COPY backend/requirements.txt ./requirements.txt
COPY backend/requirements-dev.txt ./requirements-dev.txt
RUN python -m pip wheel --wheel-dir /wheels -r requirements-dev.txt

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/app/.local/bin:${PATH}"

RUN groupadd --system app && useradd --system --gid app --create-home app

WORKDIR /app
COPY --from=builder /wheels /wheels
COPY --from=builder /build/requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels \
        -r /tmp/requirements.txt \
    && rm -rf /wheels /tmp/requirements.txt

COPY --chown=app:app backend/alembic.ini ./alembic.ini
COPY --chown=app:app backend/alembic ./alembic
COPY --chown=app:app backend/app ./app
COPY --chown=app:app --chmod=755 backend/scripts/start-api.sh ./start-api.sh

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen(f\"http://127.0.0.1:{os.environ.get('PORT', '8000')}/health\", timeout=2)"]

CMD ["./start-api.sh"]

FROM runtime AS test

USER root
COPY --from=builder /wheels /wheels
COPY --from=builder /build/requirements.txt /tmp/requirements.txt
COPY --from=builder /build/requirements-dev.txt /tmp/requirements-dev.txt
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels \
        -r /tmp/requirements-dev.txt \
    && rm -rf /wheels /tmp/requirements.txt /tmp/requirements-dev.txt
COPY --chown=app:app backend/tests ./tests
USER app

CMD ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"]

FROM runtime AS production
