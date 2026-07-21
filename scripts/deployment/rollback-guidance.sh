#!/bin/sh
set -eu
cat <<'EOF'
Safe rollback procedure:
1. Remove the failed application revision from traffic.
2. Do not run an automatic Alembic downgrade.
3. Deploy the previous image only when the applied schema is backward compatible.
4. Otherwise deploy a forward-fix migration and image.
5. Restore into a new database and smoke-test before switching traffic when data recovery is required.
See docs/operations/deployment-runbook.md.
EOF
python -m tools.check_database
