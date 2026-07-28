# Integration, UAT, and Production Deployment Runbook

## Environment strategy

`APP_ENV` explicitly selects `development`, `test`, `integration`, `uat`, `production`, or the legacy local `demo` profile. Integration, UAT, and production require PostgreSQL. UAT and production additionally require HTTPS redirects, Secure cookies, an explicit trusted-host allowlist, and the legacy local-admin adapter to be disabled.

SQLite remains supported only for local development and isolated automated tests. Never run migration validation against `sales_assistant.db`.

```powershell
python -m tools.validate_environment
```

The command redacts connection details and exits non-zero for unsafe settings.

## Configuration reference

| Variable | Purpose | Deployment rule |
|---|---|---|
| `APP_ENV` | Explicit environment | No environment guessing |
| `DATABASE_URL` / `DATABASE_URL_FILE` | PostgreSQL DSN | PostgreSQL required when deployed |
| `APPLICATION_SECRET` / `APPLICATION_SECRET_FILE` | Independent application secret | At least 32 random characters |
| `INSTAGRAM_TOKEN_ENCRYPTION_KEY` / `INSTAGRAM_TOKEN_ENCRYPTION_KEY_FILE` | Fernet key for per-Store Meta access tokens | Required and valid when deployed |
| `TRUSTED_HOSTS` | Comma-separated Host allowlist | Wildcard forbidden when deployed |
| `CORS_ALLOWED_ORIGINS` | Browser origin allowlist | Wildcard forbidden |
| `FORCE_HTTPS` | HTTPS redirect | Required in UAT/production |
| `FORWARDED_ALLOW_IPS` | Trusted reverse proxies | Never use `*` on an untrusted network |
| `SESSION_COOKIE_SECURE` | Secure cookie flag | Required in UAT/production |
| `SESSION_COOKIE_SAMESITE` | `lax` or `strict` | Default `lax` |
| `DATABASE_POOL_SIZE` | Persistent pool connections | Default 10 |
| `DATABASE_MAX_OVERFLOW` | Burst connections | Default 20 |
| `DATABASE_POOL_TIMEOUT` | Pool wait seconds | Default 30 |
| `DATABASE_POOL_RECYCLE` | Connection recycle seconds | Default 1800 |
| `LOG_FORMAT` | `auto`, `text`, or `json` | `auto` selects JSON when deployed |
| `BUILD_SHA` | Immutable build identifier | Set by CI/release tooling |

Connector credentials also accept their documented `*_FILE` variables. Mount secret files read-only and restrict them to the application user.

Generate the Instagram credential-encryption key with
`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
Back it up separately from the database. FOUNDATION-08 has no bulk
re-encryption operation, so replacing the key without first rotating every
stored connection credential makes existing ciphertext unreadable.

## Local development

```powershell
python -m pip install --requirement requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload
```

Development/test sessions preserve the legacy demo catalog. Deployed environments never auto-create demo stores, products, identities, or passwords.

## Docker integration deployment

Copy and replace placeholders locally; never commit the resulting file:

```powershell
Copy-Item .env.integration.example .env.integration
docker compose --env-file .env.integration -f compose.integration.yaml config
docker compose --env-file .env.integration -f compose.integration.yaml up --build -d
docker compose --env-file .env.integration -f compose.integration.yaml ps
```

PostgreSQL uses a persistent volume. The application runs as UID/GID `10001`, waits for PostgreSQL, validates configuration, migrates and verifies the database, then starts Uvicorn workers. Migration failure prevents startup.

## UAT and production deployment

1. Create an isolated PostgreSQL database and least-privilege application role.
2. Supply secrets through the platform secret manager or mounted files.
3. Configure a TLS-terminating proxy and exact `FORWARDED_ALLOW_IPS`.
4. For UAT/production set `FORCE_HTTPS=true`, `SESSION_COOKIE_SECURE=true`, and `LEGACY_ADMIN_ADAPTER_ENABLED=false`.
5. Validate, migrate, seed immutable system data, and bootstrap the first administrator.
6. Wait for `/ready`, then run authenticated smoke tests before enabling traffic.

## Migration procedure

```powershell
python -m tools.migration_policy
python -m tools.check_database
python -m tools.run_migrations
```

Normal deployment is forward-only. Never reset a deployed database and never automatically downgrade. The runner validates one graph head and verifies the database revision after upgrade.

## Production-safe seeds

```powershell
python -m tools.seed_data --profile production --use-configured-database
```

This creates immutable system catalogs only, never login-capable identities or business demo data.

## First platform administrator

Interactive:

```powershell
python -m tools.bootstrap_admin --email admin@example.com --display-name "Platform Administrator" --use-configured-database
```

Automation:

```powershell
$env:BOOTSTRAP_ADMIN_PASSWORD = "retrieve-from-secret-manager"
python -m tools.bootstrap_admin --email admin@example.com --display-name "Platform Administrator" --use-configured-database --password-env BOOTSTRAP_ADMIN_PASSWORD
Remove-Item Env:BOOTSTRAP_ADMIN_PASSWORD
```

The command refuses a second active platform administrator, never prints the password, assigns the explicit `platform_super_admin` role, and records audit events.

## Health and readiness

- `/live`: process liveness only.
- `/ready`: database connectivity and exact Alembic head; 503 until both pass.
- `/version`: non-sensitive version, build SHA, and environment.
- `/health`: backward-compatible health response.

Use `/ready`, not `/live`, for traffic routing.

## Deployment smoke test

```powershell
$env:SMOKE_BASE_URL = "https://uat.example.com"
$env:SMOKE_ADMIN_EMAIL = "uat-smoke@example.com"
$env:SMOKE_ADMIN_PASSWORD = "retrieve-from-secret-manager"
python -m tools.deployment_smoke --expect-empty-catalog
```

This validates liveness, readiness, build metadata, anonymous denial, login, `/auth/me`, platform RBAC, session revocation, and absence of production demo products.

## Logging

Deployed environments default to one-line JSON logs with timestamp, level, logger, message, optional event code, and correlation ID. Valid `X-Request-ID` values are returned in responses. Logs exclude request bodies, passwords, tokens, Authorization headers, connector secrets, and database URLs. Container access logging is disabled to avoid leaking query strings.

## Secret rotation

1. Create the replacement in the external secret manager.
2. Update the mounted secret or environment reference, never source control.
3. Redeploy one instance and validate readiness plus smoke tests.
4. Roll through remaining instances.
5. Revoke the previous secret at its provider.
6. Revoke affected user sessions with `tools.manage_identities` when relevant.
7. Record rotation without secret values.

Database credential rotation requires a coordinated role change and rolling connection disposal. Opaque session tokens are stored only as hashes and need no signing key.

## Backup

```sh
DATABASE_URL='postgresql://...' BACKUP_DIR=/app/backups scripts/deployment/backup.sh
```

```powershell
$env:DATABASE_URL = "postgresql://..."
.\scripts\deployment\backup.ps1 -BackupDirectory .\backups
```

Backups use compressed PostgreSQL custom format and are validated with `pg_restore --list`. Encrypt at rest, copy off-host, test restores regularly, and define retention from business RPO (for example 7 daily, 4 weekly, 12 monthly).

## Destructive restore and recovery

Always restore into a new isolated database first:

```powershell
$env:RESTORE_DATABASE_URL = "postgresql://.../isolated_restore_target"
.\scripts\deployment\restore.ps1 -BackupFile .\backups\sales-agent-TIMESTAMP.dump -ConfirmDestructiveRestore
python -m tools.run_migrations
python -m tools.deployment_smoke
```

The confirmation flag is mandatory. Validate before switching traffic. Never overwrite the only production copy.

## Rollback

Run `scripts/deployment/rollback-guidance.ps1` or `.sh`. Roll back the image only when the applied schema is backward compatible; otherwise ship a forward-fix migration. For data recovery, restore into a new database and smoke-test before switching. Automatic Alembic downgrade is deliberately unavailable.

## Troubleshooting

- Validation fails: correct the named non-secret setting; do not weaken validation.
- Connectivity fails: verify DNS, firewall, TLS, role and pool limits without printing the DSN.
- `/ready` says `out_of_date`: stop traffic and run migrations from the intended image.
- Host rejected: add the exact public hostname to `TRUSTED_HOSTS`.
- Redirect loop: trust only the proxy and ensure it sends `X-Forwarded-Proto: https`.
- Login fails: inspect sanitized audit events and lockout state; never log credentials.

## Release checklist

- [ ] Immutable reviewed image and build SHA
- [ ] Environment validation and PostgreSQL connectivity pass
- [ ] Secrets external and placeholder-free
- [ ] Backup complete and restore recently tested
- [ ] Migration policy, one head, and upgrade pass
- [ ] Production seeds create no demo identities/data
- [ ] First admin created explicitly
- [ ] `/live`, `/ready`, `/version`, and authenticated smoke pass
- [ ] CORS, hosts, HTTPS, proxy allowlist and cookies reviewed
- [ ] JSON logs reach the centralized sink
- [ ] Rollback/forward-fix owner identified
