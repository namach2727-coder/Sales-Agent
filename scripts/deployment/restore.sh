#!/bin/sh
set -eu

if [ "$#" -ne 2 ] || [ "$2" != "--confirm-destructive-restore" ]; then
  echo "Usage: restore.sh BACKUP_FILE --confirm-destructive-restore" >&2
  exit 2
fi
: "${RESTORE_DATABASE_URL:?RESTORE_DATABASE_URL is required and must identify the target database}"
pg_restore --list "$1" >/dev/null
pg_restore --exit-on-error --clean --if-exists --no-owner --no-privileges --dbname="$RESTORE_DATABASE_URL" "$1"
DATABASE_URL="$RESTORE_DATABASE_URL" python -m tools.check_database
echo "Restore completed; run migrations and deployment smoke tests before traffic is enabled."
