# DirectPilot Production Docker Deployment

This is the minimum production deployment contract for one always-on Linux
Docker host. It uses the existing modular-monolith image, a restricted public
Instagram gateway, and PostgreSQL. It does not introduce a hosting provider or
an additional infrastructure product.

## Runtime topology

`compose.production.yaml` starts exactly these application dependencies:

- `directpilot`: the complete FastAPI application on host loopback port 8000;
- `instagram-gateway`: `app.public_instagram_gateway:app`, restricted to the
  webhook, legal, and signed-public-media routes, on loopback port 8001;
- `postgresql`: PostgreSQL on the private Compose network only.

The host must provide a TLS-terminating reverse proxy. Neither application port
is bound to a public interface by default. PostgreSQL has no host port.

Ollama is intentionally absent. Production must configure the existing
provider-neutral AI interface for an external provider, or deliberately operate
an independently secured and durable Ollama endpoint. An operator laptop is
never a valid production AI dependency.

## Public ingress contract

Configure one public HTTPS hostname, `api.directpilot.ir`, with these upstreams:

| Public route | Upstream |
|---|---|
| `/api/v1/integrations/instagram/webhook` (exact path, GET and POST) | `http://127.0.0.1:8001` |
| all other paths | `http://127.0.0.1:8000` |

The exact webhook route must take precedence over the catch-all route. Do not
route arbitrary paths to port 8001. The gateway intentionally has no API docs
and does not expose the authenticated application surface.

The reverse proxy must:

- terminate TLS and redirect HTTP to HTTPS;
- preserve the original `Host`;
- set `X-Forwarded-Proto: https`;
- pass a stable request ID when available;
- use a known source address included in `FORWARDED_ALLOW_IPS`.

Never set `FORWARDED_ALLOW_IPS=*`. With a proxy container, use that container's
private subnet or fixed address. With a host proxy and published loopback ports,
`127.0.0.1` is sufficient. `TRUSTED_HOSTS` must contain only
`api.directpilot.ir`, and CORS must contain only the deployed frontend origin,
`https://directpilot.ir`.

## Configuration and secrets

Copy `.env.production.example` to `.env.production` on the host and replace all
placeholders. The destination is gitignored. Restrict it to the deployment
operator and Docker service account. The Compose file uses it for interpolation
and container environment injection; it must never be copied into an image or
source control.

At minimum, generate unique production values for the database password,
application secret, Instagram credential-encryption key, media signing secret,
Meta secrets, AI-provider credential, and commercial payment configuration.
Use the existing `*_FILE` settings instead when the host supplies mounted secret
files. Do not reuse UAT values.

Keep `META_SEND_ENABLED=false` until the production Meta application,
connection, webhook, and disposable production smoke procedure have passed.

## Persistent data

The Compose project owns four named volumes:

| Volume | Data | Required handling |
|---|---|---|
| `postgresql_data` | authoritative relational data | database backup and tested restore |
| `directpilot_media` | product/content media | filesystem backup paired with DB backup |
| `directpilot_receipts` | private payment receipts | encrypted private backup; never public |
| `directpilot_backups` | locally generated database dumps | copy off-host after every backup |

Container replacement must not delete these volumes. Never run `docker compose
down --volumes` in production. Logs and caches are intentionally ephemeral.

Create a consistent recovery point by pausing writes or using an operationally
consistent database/filesystem snapshot. Run the existing backup tool in the
application container:

```sh
docker compose --env-file .env.production -f compose.production.yaml exec \
  -T directpilot scripts/deployment/backup.sh
```

Copy the resulting validated dump plus media and receipt volume backups to
encrypted off-host storage. Test restore into a new isolated database using the
existing `scripts/deployment/restore.sh`; never overwrite the only production
copy. After restore, run migrations, `/ready`, and authenticated deployment
smoke before switching traffic.

## Deployment procedure

1. Provision the Linux host, Docker Engine with Compose v2, firewall, and a
   durable off-host backup destination.
2. Clone only the canonical backend lineage and verify the reviewed commit:

   ```sh
   git clone --branch backend-main --single-branch \
     https://github.com/namach2727-coder/Sales-Agent.git directpilot
   cd directpilot
   git rev-parse HEAD
   ```
3. Create `.env.production` from the example, replace all placeholders, keep it
   untracked, and set `BUILD_SHA` to the deployed commit.
4. Validate without printing the rendered configuration:

   ```sh
   docker compose --env-file .env.production -f compose.production.yaml config --quiet
   ```

5. Build the immutable application image:

   ```sh
   docker compose --env-file .env.production -f compose.production.yaml build
   ```

6. Take and verify a backup before every upgrade.
7. Start PostgreSQL and the application stack:

   ```sh
   docker compose --env-file .env.production -f compose.production.yaml up -d
   ```

   The application entrypoint validates production configuration, waits for
   PostgreSQL, applies the normal forward-only Alembic migration, verifies the
   revision, and fails before serving if any step fails. The gateway waits for
   the main application readiness check, so it cannot race schema migration.

8. Verify `docker compose ... ps` and confirm the database is exactly at the
   packaged migration head:

   ```sh
   docker compose --env-file .env.production -f compose.production.yaml exec \
     -T directpilot python -m tools.check_database
   ```

   Run production-safe seeds once and explicitly bootstrap the first
   administrator using the existing tools.
9. Check `/live`, `/ready`, and `/version` through the loopback-bound main
   service, and check `/privacy` plus the safe webhook verification GET through
   the restricted gateway. Run authenticated deployment smoke against the main
   service.
10. Configure DNS, TLS, and the exact ingress split only after local health and
    smoke checks pass. Repeat health and authenticated smoke through
    `https://api.directpilot.ir` and verify frontend CORS/session behavior.
11. Configure the production Meta callback and OAuth redirect only after public
    HTTPS is stable. Enable Meta outbound only in a separate controlled gate
    after all existing safety prerequisites pass.

## Rollback rule

Never run an automatic Alembic downgrade against production. If the migrated
schema remains backward compatible, roll back only to the previously reviewed
image and repeat readiness/smoke checks. Otherwise ship a forward-fix. For data
recovery, restore the validated backup into a new isolated database, migrate it
forward with the intended image, run authenticated smoke, and only then switch
traffic. The existing rollback-guidance scripts encode the same policy.

## UAT isolation

Production uses `compose.production.yaml`, project name
`directpilot-production`, `.env.production`, the `production` Docker network,
and production-prefixed named volumes. UAT keeps `compose.uat.yaml`, `.env.uat`,
its existing network, database, model, and volumes. Never point production at a
UAT database, encryption key, Meta app/account, AI endpoint, or receipt/media
volume. Do not run both stacks with an overridden identical Compose project
name.

## Minimum host baseline

- 64-bit current Linux distribution with security updates;
- Docker Engine and Docker Compose v2;
- 2 dedicated logical CPUs minimum (4 recommended);
- 4 GiB RAM minimum (8 GiB recommended for safe PostgreSQL/application headroom);
- 40 GiB SSD minimum, with capacity monitoring and separate off-host backups;
- stable public IPv4/IPv6 reachability, DNS, and ports 80/443 for the TLS proxy;
- outbound HTTPS access for Meta and the selected external AI provider.

These are initial MVP operating bounds, not proven capacity claims. Measure the
real workload before changing worker count or database pool limits.
