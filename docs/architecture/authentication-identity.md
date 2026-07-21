# Authentication, Identity, and Principal Resolution

## Scope and trust boundary

FOUNDATION-04 adds persistent human identities, Argon2id password login,
revocable opaque sessions, verified principal resolution, API dependencies, and
safe administration tooling. Authentication establishes who a caller is. The
existing RBAC engine separately decides what that verified principal may do.

The server never accepts a client-provided user ID, tenant ID, role, permission,
platform-admin flag, or membership claim as identity evidence. Only an opaque
session token resolved against the database can produce an
`AuthenticatedPrincipal`. Authorization then queries active relational RBAC
assignments again. Unknown or invalid state is denied by default.

Out of scope are public registration, MFA, email delivery, reset delivery,
social login, OAuth/OIDC providers, SSO, external identity synchronization,
service-account credentials, device trust, distributed throttling, and billing.

## Identity and password model

`UserIdentity` stores a display email and unique case-folded
`normalized_email`, display name, Argon2id hash, constrained active/disabled
status, service-account and email-verification flags, failed-login state, and
security timestamps. Normal administration disables rather than deletes users.
Password hashes are absent from every response and CLI projection. Service
accounts cannot use password login.

Email normalization trims and applies Unicode `casefold()`. The normalized value
is the unique lookup key; the submitted display email is preserved separately.
The baseline syntax check does not claim mailbox ownership. Verification
delivery is deferred.

`PasswordService` delegates to maintained `argon2-cffi` Argon2id. New passwords
are nonblank, default to at least 12 characters, and are capped at 1024
characters before expensive hashing. No arbitrary symbol rules are imposed.
Successful login detects required rehash. Missing/non-loginable users execute a
dummy Argon2 verification to reduce timing enumeration. Passwords and hashes
are never logged, audited, returned, or accepted as CLI arguments.

Changing a password or disabling a user revokes all active sessions in the same
transaction. Enabling never restores revoked sessions.

## Lockout policy

Five consecutive failures cause a default 15-minute persistent lock. Both
values are bounded settings. Successful login after expiry resets the count and
lock. External failures always return `invalid_credentials`, whether the user is
missing, disabled, locked, a service account, or has a wrong password. Unknown
emails are not stored in audit metadata. Distributed/network throttling remains
required before production.

## Opaque session lifecycle

`secrets.token_urlsafe(48)` creates an opaque token returned only at login. The
database stores only its SHA-256 digest, protected by a unique index. Each
`AuthSession` has a UUID, owner, constrained active/revoked/expired status,
expiry/revocation/last-seen timestamps, and optional hashed user-agent metadata.
Raw IPs and full user agents are not stored.

Resolution rejects malformed, unknown, expired, revoked, and disabled-user
sessions. One or all sessions can be revoked. Session list responses expose
sanitized metadata, never raw tokens or hashes.

## Principal resolution and RBAC

The immutable `AuthenticatedPrincipal` contains verified user/display identity,
session ID/time, active platform roles, and server-resolved Store memberships
with active tenant roles. It contains no credential.

Request flow:

1. extract a bearer token or configured HttpOnly cookie, never a query value;
2. hash/resolve token and verify status/expiry;
3. verify the persistent user is active;
4. load platform roles and tenant membership/roles from the database;
5. build the immutable principal;
6. resolve trusted tenant context server-side;
7. convert to FOUNDATION-03 `AuthorizationPrincipal`;
8. invoke `AuthorizationService` for the explicit permission.

Client role and tenant headers are ignored. Membership alone grants no
permission. Inactive memberships and assignments are ineffective.

The existing `TenantMembership` gains nullable indexed `user_id` and unique
`(tenant_id, user_id)`. Persistent membership also records the compatible
principal tuple `("user", str(user_id))`; existing RBAC assignments are reused.
Provisioning still creates no owner. Operators explicitly add membership and
then assign a tenant role.

## FastAPI API and cookie policy

Dependencies include `optional_current_principal`,
`require_authenticated_principal`, `require_platform_permission(code)`, and
`require_tenant_permission(code)`. The permission dependencies reuse RBAC.

Endpoints are `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`,
`GET /auth/sessions`, and `DELETE /auth/sessions/{session_id}/revoke`. There is
no registration. Login returns a bearer token once and sets an HttpOnly,
SameSite=Lax, explicit-Max-Age cookie that defaults to Secure. Local HTTP must
explicitly set `SESSION_COOKIE_SECURE=false`.

SameSite reduces but does not replace CSRF defenses. Future cookie-authenticated
mutations must adopt same-origin/Fetch Metadata or a dedicated CSRF-token
policy. Bearer clients must protect tokens. HTTP semantics use 401 for invalid
authentication, 403 for insufficient permission, 409 for safe administration
conflicts, and 422 for malformed input; login errors do not enumerate accounts.

## Provider-admin transition

High-risk provider routes now accept a verified persistent principal with the
required platform permission. With no session, the existing development-only
loopback adapter may run only when `legacy_admin_adapter_enabled` is true.
Invalid supplied sessions never fall back. The adapter retains original
same-origin controls and finite RBAC role. It is transitional, not a production
bypass, and no privilege is inferred from email.

## Audit and seed privacy

`IdentityAuditLog` records sanitized identity creation/status/password changes,
login success/failure, session creation/revocation, all-session revocation, and
membership changes. It stores applicable numeric actor/target, tenant/session
IDs, outcome, reason and timestamp. It never stores an unknown login email,
password/hash, token/hash, cookie, authorization header, URL, IP, raw user agent,
payload, or stack trace.

`development.disabled_identity_placeholder` is create-only and compatible only
with development/demo/test. It creates a disabled passwordless `.invalid`
placeholder. It is not production-safe and cannot log in. No production user,
password, membership, role, session, token, or credential is seeded.

## CLI

`python -m tools.manage_identities` supports `create-user`, `list-users`,
`show-user`, enable/disable, `set-password`, membership add/disable/list,
session revoke/all-revoke, and `show-effective-access`. Execution requires an
explicit database selection. Passwords use `getpass` plus confirmation and are
never command arguments. JSON is sanitized. Exit codes are 0 success, 1
database/execution, 2 validation, and 3 conflict.

## Migration and deployment

`0004_authentication_identity` follows `0003_authorization_rbac`, creates
`user_identities`, `auth_sessions`, and `identity_audit_logs`, and extends
`tenant_memberships`. No user data is embedded. SQLite validates migration
shape; PostgreSQL must test concurrent email creation, token uniqueness,
revocation/password races, locks, and audit rollback.

Production checklist: migrate staging, run policy/PostgreSQL tests, keep Secure
cookies under HTTPS, configure TTL/password/lockout, run production-safe seeds,
create the first user interactively, assign platform role explicitly, verify
login/denial/revocation/audit, deploy edge throttling, then remove the legacy
adapter after persistent administration is proven.

## Deferred work

- MFA and recovery codes
- email verification and password-reset delivery
- social login, OAuth/OIDC, SSO, and external identity synchronization
- distributed login/network throttling
- device trust and risk scoring
- service-account/API-key credentials
- refresh-token rotation if JWT is ever introduced
- session/device notification delivery
- elevated cross-user session administration API
