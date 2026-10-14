#!/bin/sh
# This entrypoint deliberately SKIPS migrations and any one-shot write jobs.
# Migrations are a separately approved, single-operator procedure.
set -eu
python -m tools.full_render_exit_guard
: "${DP_ENTRYPOINT_APP:?DP_ENTRYPOINT_APP is required}"
exec uvicorn "${DP_ENTRYPOINT_APP}" \
  --host 0.0.0.0 \
  --port "${DP_ENTRYPOINT_PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-1}" \
  --proxy-headers \
  --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-127.0.0.1}" \
  --no-access-log
