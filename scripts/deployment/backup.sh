#!/bin/sh
set -eu

: "${DATABASE_URL:?DATABASE_URL is required}"
BACKUP_DIR="${BACKUP_DIR:-/app/backups}"
mkdir -p "$BACKUP_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET="$BACKUP_DIR/sales-agent-$STAMP.dump"
pg_dump --format=custom --compress=9 --no-owner --no-privileges --file="$TARGET" "$DATABASE_URL"
pg_restore --list "$TARGET" >/dev/null
echo "Backup created and validated: $TARGET"
