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

if [ "${DIRECTPILOT_BOOTSTRAP_ADMIN_ON_START:-false}" = "true" ]; then
  : "${DIRECTPILOT_BOOTSTRAP_ADMIN_EMAIL:?DIRECTPILOT_BOOTSTRAP_ADMIN_EMAIL is required}"
  : "${DIRECTPILOT_BOOTSTRAP_ADMIN_DISPLAY_NAME:?DIRECTPILOT_BOOTSTRAP_ADMIN_DISPLAY_NAME is required}"
  : "${DIRECTPILOT_BOOTSTRAP_ADMIN_PASSWORD:?DIRECTPILOT_BOOTSTRAP_ADMIN_PASSWORD is required}"

  echo "Running one-shot platform administrator bootstrap..."
  python -m tools.bootstrap_admin \
    --email "$DIRECTPILOT_BOOTSTRAP_ADMIN_EMAIL" \
    --display-name "$DIRECTPILOT_BOOTSTRAP_ADMIN_DISPLAY_NAME" \
    --use-configured-database \
    --password-env DIRECTPILOT_BOOTSTRAP_ADMIN_PASSWORD
fi


if [ "${DIRECTPILOT_RESET_ADMIN_PASSWORD_ON_START:-false}" = "true" ]; then
  : "${DIRECTPILOT_RESET_ADMIN_EMAIL:?DIRECTPILOT_RESET_ADMIN_EMAIL is required}"
  : "${DIRECTPILOT_RESET_ADMIN_PASSWORD:?DIRECTPILOT_RESET_ADMIN_PASSWORD is required}"

  echo "Running one-shot platform administrator password reset..."
  python -m tools.reset_admin_password \
    --email "$DIRECTPILOT_RESET_ADMIN_EMAIL" \
    --use-configured-database \
    --password-env DIRECTPILOT_RESET_ADMIN_PASSWORD
fi

echo "Starting application..."
exec uvicorn app.main:app \
  --host "${HOST:-0.0.0.0}" \
  --port "${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --proxy-headers \
  --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-127.0.0.1}" \
  --no-access-log
