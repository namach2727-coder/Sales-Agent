#!/bin/sh
set -eu

echo "Validating deployment environment..."
python -m tools.validate_environment

attempt=1
until python -m tools.check_database; do
  if [ "$attempt" -ge 30 ]; then
    echo "ERROR database did not become available" >&2
    exit 1
  fi
  attempt=$((attempt + 1))
  sleep 2
done

python -m tools.run_migrations

if [ "${DIRECTPILOT_SEED_ON_START:-false}" = "true" ]; then
  echo "Running controlled production seed..."
  python -m tools.seed_data --profile production --use-configured-database
fi

echo "Starting application..."
exec uvicorn app.main:app \
  --host "${HOST:-0.0.0.0}" \
  --port "${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --proxy-headers \
  --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-127.0.0.1}" \
  --no-access-log
