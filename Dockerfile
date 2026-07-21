FROM python:3.12.10-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install --no-install-recommends -y postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home --shell /usr/sbin/nologin app

WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --requirement requirements.txt

COPY --chown=app:app . .
RUN chmod 0555 scripts/deployment/docker-entrypoint.sh \
    && mkdir -p /app/private_media /app/backups \
    && chown -R app:app /app/private_media /app/backups

USER app
EXPOSE 8000
ENTRYPOINT ["/app/scripts/deployment/docker-entrypoint.sh"]
