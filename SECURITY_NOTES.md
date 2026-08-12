# DirectPilot MVP Security Notes

## Implemented controls

- Argon2id passwords, opaque expiring/revocable sessions and login lockout.
- Permission-based platform/tenant authorization and public-ID API boundaries.
- Tenant/store filters and compound persistence constraints on scoped data.
- Backend-authoritative plan prices and admin-only payment decisions.
- Private validated receipt storage with non-enumerable keys.
- Single-use, expiring, hash-only OAuth state bound to tenant/store/user.
- Fernet-encrypted per-store Instagram tokens; no token in response schemas.
- Meta signature verification, event deduplication and restricted webhook app.
- Shared `META_SEND_ENABLED` fail-closed outbound boundary.
- Credential-free audit events and redacted operational logging.

## Residual risks before production

- Local filesystem receipt storage is not a production object-store/HA design.
- OAuth callback and login endpoints need infrastructure rate limits/WAF rules;
  application login lockout exists but is not distributed.
- Customer account email verification/recovery is not a complete production
  lifecycle.
- Multi-membership customer scope currently selects the first active membership;
  first-pilot registration creates one tenant, but explicit tenant selection is
  needed before broader multi-tenant self-service.
- Production Meta app review, token lifecycle monitoring and revocation handling
  require operator validation.
- Privacy/legal and retention/deletion policy require business sign-off.

No claim of perfect security is made. Production activation requires the
deployment prerequisites and a focused review of actual hosting controls.
