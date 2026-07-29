# PostgreSQL compatibility testing

The PostgreSQL suite is an explicit, local-only validation path. Pytest will
not use PostgreSQL from `DATABASE_URL` alone. It requires
`DIRECTPILOT_POSTGRES_TEST_URL`, validates that the URL uses PostgreSQL, requires
credentials and a host, and requires the database name to end in `_test`.

## Start PostgreSQL 16

```powershell
docker compose -f compose.postgres-test.yaml up -d --wait
```

The test-only Compose service exposes PostgreSQL on port `55432` by default,
uses the dedicated `directpilot_test` database and credentials, and has no
production persistence configuration.

## Configure the explicit test URL

```powershell
$env:DIRECTPILOT_POSTGRES_TEST_URL = `
  "postgresql+psycopg://directpilot_test:directpilot_test@127.0.0.1:55432/directpilot_test"
$env:DATABASE_URL = $env:DIRECTPILOT_POSTGRES_TEST_URL
$env:APP_ENV = "test"
```

`DATABASE_URL` is needed by Alembic. Pytest independently requires
`DIRECTPILOT_POSTGRES_TEST_URL` and replaces its application database URL with
that validated value before importing the application database module.

## Migrate an empty test database

```powershell
python -m alembic upgrade head
python -m alembic current
```

The expected current revision is:

```text
0009_conversation_core_models (head)
```

Pytest refuses to continue if the PostgreSQL database is not already at that
revision.

## Run the suite

```powershell
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
python -m pytest
```

Pytest opts in exclusively through `DIRECTPILOT_POSTGRES_TEST_URL`, uses that
validated URL to construct the global application engine, and then removes the
temporary `DATABASE_URL` override so it cannot leak into configuration-isolation
tests. A small number of dialect-specific unit tests intentionally continue to
construct private SQLite engines; these preserve development compatibility and
do not access the normal development database.

## Reset to an empty database

```powershell
docker compose -f compose.postgres-test.yaml down
docker compose -f compose.postgres-test.yaml up -d --wait
```

Because the test Compose file declares no volume, recreating the container
starts from an empty test database. Stop it after validation:

```powershell
docker compose -f compose.postgres-test.yaml down
```
