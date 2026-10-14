# DirectPilot — UAT-only private object-media integration (2026-10-14)

## Scope and hard boundaries

- Feature branch: `feature/vercel-uat-durable-s3-media`, based on experimental UAT Vercel FastAPI branch `migration/vercel-uat-fastapi-20261014`. This is NOT part of Render Production, `backend-main`, or the existing deployed UAT API until separately promoted and tested.
- New product images (distinct from payment receipts) can be stored in a private S3-compatible object store such as Cloudflare R2 using `app/object_media_storage.py`. Existing media metadata table and object key format remain unchanged; no DB migration required.
- `MEDIA_STORAGE_BACKEND=local` remains the compatibility default on traditional Docker hosts. On Vercel Functions (`VERCEL=1`), local product-media uploads **fail closed with HTTP 503** rather than claiming persistent disk storage.
- Receipt files continue to be stored in `manual_payments.receipt_data` in PostgreSQL; the implementation does not alter receipt storage.
- Publishing to Meta stays DISABLED. A signed API media URL redirecting to a short-lived private S3 GET URL needs controlled remote fetch / Meta compatibility tests before enabling sends. No production callbacks, media or credentials changed.

## Operator prerequisites — no credentials in chat or Git

Create an **independent, private UAT bucket** in a commercially permissible S3-compatible service. Cloudflare R2 is an example, not a configured dependency. Generate a narrowly bucket-scoped read/write API token and store credentials as Sensitive Vercel Environment Variables for the existing **isolated** `directpilot-uat-api` Vercel project (target `Production` labels the UAT-only project runtime).

| Environment variable | Example / meaning |
|---|---|
| `MEDIA_STORAGE_BACKEND` | `s3` |
| `MEDIA_S3_ENDPOINT_URL` | `https://<account-id>.r2.cloudflarestorage.com` (origin only; no embedded credentials) |
| `MEDIA_S3_REGION` | `auto` for R2 |
| `MEDIA_S3_BUCKET` | Private UAT bucket name |
| `MEDIA_S3_PREFIX` | `uat` (must be different from Production) |
| `MEDIA_S3_ACCESS_KEY_ID` | Restricted, private access key (Sensitive) |
| `MEDIA_S3_SECRET_ACCESS_KEY` | Restricted, private secret (Sensitive) |
| `PUBLIC_MEDIA_BASE_URL` | Trusted HTTPS origin of isolated UAT Backend; no trailing path |
| `MEDIA_SIGNING_SECRET` | Dedicated strong random signing secret (Sensitive), distinct from DB credential |

Do not set these variables in the shared frontend, Render Production or Neon Postgres. Do not expose bucket/object listings to the public. Do not use a Production bucket or production credentials for UAT.

## Runtime behavior and limits

1. Manager/admin saves validated JPEG. The API creates opaque `store-<store-id>/<uuid>.jpg`, uploads bytes to `<prefix>/<key>` with private cache-control, and persists `ProductMediaAsset` metadata in UAT PostgreSQL.
2. Admin preview first enforces existing application authentication/RBAC and returns a short-lived (60-second) redirect to an S3 pre-signed GET URL. Do not copy/store the redirect target or log its signature.
3. Public media route verifies existing HMAC/expiry, asset status, then returns a pre-signed 302 GET URL (up to 900s). The bucket itself stays private. Validate that the remote Meta image fetch supports this redirect **without actual publication** before enabling `META_SEND_ENABLED`.
4. Delete checks existing approved/publishing/published references and removes the stored object before marking metadata deleted; errors fail without marking successful deletion.
5. Vercel Functions impose a request-body cap (documented as 4.5 MB). Legacy JSON/base64 JPEG uploads up to 8 MiB **cannot be assumed supported**. A serverless image-size guard limits decoded JPEGs to 3 MiB, but oversized requests may be rejected upstream before application validation. Production-quality larger-image support requires a tenant-verified direct-to-bucket presigned upload/finalize workflow with content hashing and authorization. This remains OPEN.
6. Existing historical media on local Render disk are NOT automatically migrated. Inventory/transfer and verify object integrity and signed-link compatibility before retiring either source.
7. External bucket availability, transfer latency, data retention, signed links and real Vercel runtime behavior must be tested with dummy UAT media after provisioning. There is no production readiness claim from source-code tests alone.

## Acceptance checklist

- [ ] UAT bucket configured and restricted access validated; explicit owner acknowledgment of any required billing.
- [ ] GitHub CI tests and review of S3 adapter/ACL behavior PASS; no dynamic unreviewed code or secrets in Git.
- [ ] Branch deployed ONLY to isolated Vercel UAT Backend, after target/environment check.
- [ ] A small dummy JPEG uploads successfully; database row and object digest match; no local ephemeral image storage.
- [ ] Admin authenticated preview works, unauthenticated preview denied, expiring R2 URL revoked by TTL.
- [ ] Public HMAC link serves the intended image via redirect and rejects tampering/expiry.
- [ ] After redeploy/cold start, image remains retrievable.
- [ ] Delete marks record deleted, removes remote object, and links no longer resolve.
- [ ] Limits and response behavior for >3 MiB via browser documented; no UI silently reporting success.
- [ ] Production media inventory/rollback tested separately; Meta actual-send toggle remains OFF.
- [ ] Explicit decision on commercially permitted Backend hosting and Neon storage/compute before Production transfer.

## Backout and constraints

Existing Render APIs and source database are untouched. To roll back isolated UAT deployment, redeploy the previously accepted API commit after verifying no new UAT-only media objects require the S3 adapter; never delete new persistent UAT images during rollback. Never point Prod to UAT bucket, Neon UAT, or old stale Neon rehearsal DB.
