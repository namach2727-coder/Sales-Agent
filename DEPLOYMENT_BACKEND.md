# DirectPilot Backend Deployment

## Production target

Use a stable long-running Python/container host for `api.directpilot.ir`, not a
short-lived frontend function runtime. Required components are the DirectPilot
application, restricted public Instagram gateway, managed PostgreSQL, private
object storage for receipts and the selected LLM runtime/provider.

## Release procedure

1. Build an immutable image and record `BUILD_SHA`.
2. Supply secrets through the hosting secret facility, never the image or Git.
3. Back up PostgreSQL and prove the restore path.
4. Run `alembic upgrade head` as a single controlled release step.
5. Start application and gateway with restart policies.
6. Require `/health` and `/ready` before traffic.
7. Configure HTTPS, explicit trusted hosts, CORS only for
   `https://directpilot.ir`, secure cookies and forwarded proxy allowlist.
8. Point the stable Meta webhook to the restricted gateway only.
9. Keep `META_SEND_ENABLED=false` until production connection verification and
   explicit go-live approval.
10. Run deployment smoke, then monitor credential-free structured logs.

## External prerequisites

- hosting account and stable HTTPS endpoint;
- managed PostgreSQL project (Supabase PostgreSQL is acceptable via standard
  `DATABASE_URL`, without Supabase domain coupling);
- private object storage and backup/restore ownership;
- DNS for `api.directpilot.ir`;
- Meta production app review/business requirements;
- privacy policy, terms, deletion process and operator incident contacts.

UAT volumes/databases must not be deleted or recreated during release work.
