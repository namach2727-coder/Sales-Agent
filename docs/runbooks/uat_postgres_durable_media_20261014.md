# DirectPilot UAT: durable product images in PostgreSQL — 2026-10-14

## PERMANENT OWNER DECISION — read before any new-chat action
- **DO NOT suggest, implement, provision, or request credentials for Cloudflare R2/S3/Blob media storage.** User explicitly chose PostgreSQL/Neon `BYTEA` for product images, matching the existing PostgreSQL `manual_payments.receipt_data` implementation.
- Superseded R2 PR #33 was CLOSED WITHOUT MERGE; do not resurrect. This is a binding product decision unless the owner explicitly changes it.
- UAT and Production data/projects are independent. Production Render remains authoritative; the final Production dump/backup/write-freeze/event-replay/reconciliation/rollback/cutover remain separate, blocked gates. Do not make production changes when validating UAT.
- Standard chat handoff documents: `AI_HANDOFF.md`, `PROJECT_ROADMAP.md`, `DECISIONS.md`, `CURRENT_STATE.md`, `NEXT_ACTIONS.md`. Read them first, then deployed facts; never require owner to explain this decision again.

## Implementation in isolated UAT feature branch
- Base API branch: `migration/vercel-uat-fastapi-20261014`.
- UAT feature branch: `feature/uat-postgres-durable-product-media-20261014`.
- Alembic revision: `0026_durable_product_media`, parent `0025_trial_three_days`. Additive nullable `product_media_assets.image_data` `BYTEA` (`LargeBinary` in SQLAlchemy). `deferred=True` on ORM avoids downloading image bytes for catalog lists; older rows preserved.
- New JPEG uploads: validate magic, dimensions, format and 2 MiB decoded byte maximum (base64 JSON overhead within Vercel's 4.5 MiB body limit) and 50 MiB per-store active-image quota. Save bytes+metadata atomically in PostgreSQL. Object key is opaque `db:<uuid>.jpg`; no dependency on local disk/R2.
- Private admin preview: authenticated/admin authorization and module guard from existing routing; bytes served via `Response(image/jpeg)`, `Cache-Control: no-store`. Legacy local-disk-only assets remain fallbacks ONLY on hosts retaining the old files.
- Public signed media route: preserve existing HMAC, short expiry and ready-status validation, then serve bytes from PostgreSQL with JPEG type. This endpoint is not an unauthenticated list/browse service; valid signed URL is required. META_SEND remains disabled.
- Deletion: preserve existing approved/publishing/published draft protection; clear image_data and mark deleted, revoke future authorization to read it; still delete legacy local file when applicable.
- RECEIPTS UNCHANGED: payment receipt bytes stay in `manual_payments.receipt_data` in PostgreSQL; admin receipt approvals and authorization untouched.

## Operations / testing checklist
1. [ ] GitHub PR CI all PASS, including SQLite fresh schema, PostgreSQL 18 migration check and unit tests for upload, read via fresh SQLAlchemy session, signed URL, tampering, deletion, size.
2. [ ] Keep feature code UAT-only until tested. **Do NOT deploy updated ORM to UAT Neon head 0025 before applying reviewed Alembic 0026**: `/ready` checks for migration head, and FastAPI startup must not run auto-migrate.
3. [ ] Take independent, tested recoverable **UAT** DB backup/snapshot before modifying populated UAT `neondb`. Neon project `round-shape-42044596`; Production Neon `billowing-poetry-05589994` must not be touched.
4. [ ] In controlled UAT maintenance, apply exactly `0026_durable_product_media` after validating base `0025_trial_three_days` and DB target identity. Ensure no other Alembic heads or unexpected writers. Before/after capture table counts, migrations, media metadata and sample hashes.
5. [ ] Deploy only to isolated Vercel `directpilot-uat-api` project and validate `/live`, `/ready` and isolated frontend Preview (not shared `uat.directpilot.ir` and not `directpilot.ir`). Disable Meta sends/payments.
6. [ ] Use one **dummy** JPEG <=2 MiB: upload through authorized UAT manager endpoint, preview from new function/cold restart, signed route and expiry, delete; verify PostgreSQL bytea and counts without disclosing customer content.
7. [ ] Check Neon Free quota: 1 GiB/project (subject to provider current terms), 2 MiB/image × max 10 images/product can exhaust storage. The code enforces 50 MiB active images per store, but database-wide usage, backups and retention must still be measured before Production.
8. [ ] Ensure real Meta image-fetch semantics and Vercel Function latency/response-size limits before any real publishing. Production commercial hosting plan (Vercel Hobby restrictions) is a separate gate.
9. [ ] No Render shutdown, no DNS/Meta redirects, no Production DB cutover without independently verified final freeze/replay/backup/parity and owner GO.

## Evidence boundaries
- Code committed/CI PASS is not operational UAT acceptance. Runtime changes must be measured and reported separately.
- Empty `product_media_assets` in UAT as of 2026-10-14 is a point-in-time read-only count, not a promise that any other database has no existing legacy media.
