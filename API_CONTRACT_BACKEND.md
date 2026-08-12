# DirectPilot Backend API Contract

This is the backend source of truth for the `directpilot-web` MVP integration.

- Production API origin: `https://api.directpilot.ir`
- API prefix: `/api/v1`
- Media type, except receipt bytes: `application/json`
- Resource identifiers: public UUID strings only
- Date/time values: ISO 8601 strings with timezone information
- Money: integer IRR values; the backend is authoritative

The legacy `/auth/*` routes are not part of this contract. Browser clients must
use `/api/v1/auth/*`, whose responses do not expose internal numeric IDs.

## Authentication transport

Login creates an opaque server-side session and provides it in two transports:

1. `Set-Cookie: sales_agent_session=...; Path=/; HttpOnly; Secure; SameSite=Lax`
2. the `access_token` field of the JSON response, usable as
   `Authorization: Bearer <opaque-token>`

The production browser contract is the **HttpOnly session cookie**. The frontend
must send `credentials: "include"` on login and every authenticated request. It
must not persist `access_token` in local storage, session storage, IndexedDB, or
JavaScript-readable cookies. Bearer transport remains available for non-browser
clients.

The cookie is host-only because no `Domain` attribute is set. It is stored for
`api.directpilot.ir`, not exposed to `directpilot.ir`, and is sent to the API by
credentialed browser requests. Both origins are HTTPS and same-site while still
being cross-origin, so production CORS must explicitly allow the web origin.

## Common errors

Domain/authentication failures use this stable envelope:

```json
{
  "detail": {
    "code": "stable_machine_code",
    "message": "safe human-readable message"
  }
}
```

Common codes and statuses:

| HTTP | Code | Meaning |
|---:|---|---|
| 400 | `invalid_oauth_state` | Instagram OAuth state is invalid, expired, or consumed |
| 401 | `invalid_credentials` | Login failed |
| 401 | `authentication_required` | No supported credential was provided |
| 401 | `invalid_session` | Session is invalid, revoked, or expired |
| 403 | `forbidden` | Tenant/store access is not active |
| 403 | `instagram_entitlement_required` | Plan does not permit another Instagram account |
| 404 | `not_found` | Caller-owned resource was not found |
| 409 | `conflict` | State conflict, duplicate, or invalid transition |
| 409 | `instagram_connection_conflict` | Instagram account conflicts with an existing connection |
| 413 | `receipt_too_large` | Receipt exceeds configured byte limit |
| 422 | `validation_error` | Commerce business validation failed |
| 422 | `invalid_receipt` | Receipt type/signature is invalid |
| 422 | `instagram_onboarding_error` | Instagram onboarding validation failed |
| 502 | `instagram_provider_error` | Sanitized Meta provider failure |
| 503 | `authentication_unavailable` | Authentication is disabled/unavailable |
| 503 | `payment_provider_unavailable` | Card-transfer instructions are not configured |

FastAPI/Pydantic request-shape failures also return HTTP 422, using FastAPI's
standard `{"detail":[...]}` validation list rather than the domain envelope.
Clients must handle both 422 shapes.

## Endpoint summary

| Area | Method | Path | Auth | Success |
|---|---|---|---|---:|
| Auth | POST | `/api/v1/auth/register` | Public | 201 |
| Auth | POST | `/api/v1/auth/login` | Public | 200 |
| Auth | POST | `/api/v1/auth/logout` | Session | 200 |
| Auth | GET | `/api/v1/auth/me` | Session | 200 |
| Plans | GET | `/api/v1/plans` | Public | 200 |
| Orders | POST | `/api/v1/orders` | Session | 201 |
| Orders | GET | `/api/v1/orders/me` | Session | 200 |
| Orders | GET | `/api/v1/orders/{order_public_id}` | Session | 200 |
| Payments | POST | `/api/v1/payments/card-transfer` | Session | 201 |
| Payments | POST | `/api/v1/payments/{payment_public_id}/receipt` | Session | 200 |
| Payments | GET | `/api/v1/payments/me` | Session | 200 |
| Subscription | GET | `/api/v1/subscription/me` | Session | 200 |
| Instagram | POST | `/api/v1/integrations/instagram/connect` | Session + entitlement | 200 |
| Instagram | GET | `/api/v1/integrations/instagram/callback` | One-time OAuth state | 200 |
| Instagram | GET | `/api/v1/integrations/instagram/status` | Session | 200 |
| Instagram | GET | `/api/v1/integrations/instagram/accounts` | Session | 200 |

## Authentication

### POST `/api/v1/auth/register`

Request:

```json
{
  "email": "owner@example.com",
  "password": "a-production-password",
  "display_name": "Store Owner",
  "tenant_name": "Example Business",
  "tenant_slug": "example-business",
  "store_name": "Example Store",
  "store_slug": "example-store"
}
```

Field limits: email 3–320, password request 1–4096 (runtime password policy is
authoritative; production minimum is 12), display/tenant/store names 2–200,
tenant/store slugs 2–63.

Response 201:

```json
{
  "email": "owner@example.com",
  "display_name": "Store Owner",
  "tenant_public_id": "00000000-0000-0000-0000-000000000001",
  "tenant_slug": "example-business",
  "store_public_id": "00000000-0000-0000-0000-000000000002",
  "store_slug": "example-store"
}
```

Registration does not authenticate the browser. Follow it with login. Duplicate
identity/slug conflicts return 409; validation failures return 422.

### POST `/api/v1/auth/login`

Request: `{"email":"owner@example.com","password":"..."}`.

Response 200 sets the session cookie and returns:

```json
{
  "access_token": "<opaque-session-token>",
  "token_type": "bearer",
  "expires_at": "2026-08-12T12:00:00Z",
  "principal": {
    "email": "owner@example.com",
    "display_name": "Store Owner",
    "session_public_id": "00000000-0000-0000-0000-000000000003",
    "authenticated_at": "2026-08-12T04:00:00Z",
    "tenant_memberships": [{
      "tenant_public_id": "00000000-0000-0000-0000-000000000001",
      "tenant_slug": "example-business",
      "status": "active"
    }]
  }
}
```

Bad credentials return 401 `invalid_credentials`.

### POST `/api/v1/auth/logout`

Revokes the server session, expires the cookie, and returns 200:
`{"status":"revoked"}`.

### GET `/api/v1/auth/me`

Returns the same public `principal` object shape used by login (without the
outer token fields). Use this endpoint to restore browser authentication state.

## Plans

### GET `/api/v1/plans`

Returns 200 with an array of active plans:

```json
[
  {
    "public_id": "00000000-0000-0000-0000-000000000010",
    "code": "START",
    "name": "Start",
    "price_amount": 2990000,
    "currency": "IRR",
    "reply_limit": 1500,
    "automation_limit": 10,
    "instagram_account_limit": 1,
    "duration_days": 30
  }
]
```

The frontend must render values returned by this endpoint rather than embed
commercial amounts or limits.

## Orders

### POST `/api/v1/orders`

Request: `{"plan_public_id":"<36-character-public-id>"}`.

Response 201:

```json
{
  "public_id": "00000000-0000-0000-0000-000000000020",
  "tenant_public_id": "00000000-0000-0000-0000-000000000001",
  "store_public_id": "00000000-0000-0000-0000-000000000002",
  "plan_public_id": "00000000-0000-0000-0000-000000000010",
  "plan_code": "START",
  "status": "pending_payment",
  "price_amount": 2990000,
  "currency": "IRR",
  "created_at": "2026-08-12T04:00:00Z"
}
```

No price field is accepted. The backend snapshots the authoritative plan price.
A zero-price plan activates the resulting subscription during order creation.

### GET `/api/v1/orders/me`

Returns 200 with caller-owned orders, each using `OrderRead` above.

### GET `/api/v1/orders/{order_public_id}`

Returns one caller-owned order or 404. Cross-tenant resources are not exposed.

## Card-transfer payments

### POST `/api/v1/payments/card-transfer`

Request: `{"order_public_id":"<36-character-public-id>"}`.

Response 201:

```json
{
  "payment": {
    "public_id": "00000000-0000-0000-0000-000000000030",
    "order_public_id": "00000000-0000-0000-0000-000000000020",
    "status": "pending",
    "amount": 2990000,
    "currency": "IRR",
    "revision": 1,
    "receipt_configured": false,
    "created_at": "2026-08-12T04:01:00Z"
  },
  "card_number": "<configured-card-number>",
  "account_number": "<configured-account-number>",
  "account_name": "<configured-account-holder>",
  "bank_name": "<configured-bank>",
  "instructions": "<configured-customer-instructions>"
}
```

Only these customer-facing transfer fields and the authoritative order/payment
amount are returned. Unrelated financial configuration is never exposed.

### POST `/api/v1/payments/{payment_public_id}/receipt`

This endpoint **does not accept multipart/form-data**. Its request body is the
raw file bytes. Supported media types are `image/jpeg`, `image/png`, and
`application/pdf`; the declared content type must match validated magic bytes.
The configured default maximum is 5 MiB.

On success it returns 200 with `PaymentRead`, normally with status `submitted`
and `receipt_configured: true`. Receipts remain in private storage and have no
public customer download URL.

### GET `/api/v1/payments/me`

Returns 200 with caller-owned `PaymentRead` objects. Provider approval/rejection
is permission-protected and outside the customer frontend contract. Approval
atomically marks the order paid and activates the subscription.

## Subscription

### GET `/api/v1/subscription/me`

Returns 200 with either `null` or:

```json
{
  "public_id": "00000000-0000-0000-0000-000000000040",
  "tenant_public_id": "00000000-0000-0000-0000-000000000001",
  "store_public_id": "00000000-0000-0000-0000-000000000002",
  "plan_public_id": "00000000-0000-0000-0000-000000000010",
  "plan_code": "START",
  "status": "active",
  "limits": {
    "reply_limit": 1500,
    "automation_limit": 10,
    "instagram_account_limit": 1
  },
  "starts_at": "2026-08-12T04:05:00Z",
  "current_period_end": "2026-09-11T04:05:00Z"
}
```

## Instagram OAuth onboarding

This backend implements the official **Instagram API with Instagram Login**.
The requested scopes are `instagram_business_basic`,
`instagram_business_manage_messages`, and
`instagram_business_manage_comments`.

### POST `/api/v1/integrations/instagram/connect`

No request body. The authenticated tenant/store must have subscription
entitlement and available account capacity. Returns 200:

```json
{
  "authorization_url": "https://www.instagram.com/oauth/authorize?...",
  "expires_at": "2026-08-12T04:10:00Z"
}
```

The frontend navigates the user to `authorization_url`. OAuth state is generated
and validated by the backend and must not be created or interpreted by the
frontend.

### GET `/api/v1/integrations/instagram/callback?code=...&state=...`

Meta redirects to the API callback configured as
`https://api.directpilot.ir/api/v1/integrations/instagram/callback`. The callback
uses the one-time state, exchanges the code, and creates/updates the encrypted
connection. It currently returns 200 JSON rather than redirecting to a frontend
route:

```json
{
  "connection_public_id": "00000000-0000-0000-0000-000000000050",
  "tenant_public_id": "00000000-0000-0000-0000-000000000001",
  "store_public_id": "00000000-0000-0000-0000-000000000002",
  "instagram_username": "example_store",
  "status": "active"
}
```

The callback does not require the browser session; the signed, expiring,
single-use state identifies the pending flow. Provider failures return a
sanitized 502 and never expose Meta response credentials.

### GET `/api/v1/integrations/instagram/status`

Returns entitlement, capacity, connected count, and safe account records:

```json
{
  "entitled": true,
  "account_limit": 1,
  "connected_accounts": 1,
  "accounts": [{
    "connection_public_id": "00000000-0000-0000-0000-000000000050",
    "instagram_username": "example_store",
    "status": "active",
    "token_configured": true,
    "connected_at": "2026-08-12T04:10:00Z"
  }]
}
```

### GET `/api/v1/integrations/instagram/accounts`

Returns 200 with only the tenant/store-scoped `accounts` array shape above.

## Production browser and CORS contract

Required production backend values:

```dotenv
TRUSTED_HOSTS=api.directpilot.ir
CORS_ALLOWED_ORIGINS=https://directpilot.ir
FORCE_HTTPS=true
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=lax
```

The API middleware allows credentials, the exact web origin, methods
`GET, POST, PUT, PATCH, DELETE, OPTIONS`, and headers `Accept`, `Content-Type`,
`Authorization`, `X-Request-ID`, and `X-CSRF-Token`. Wildcard origins are
rejected for deployed profiles. The frontend must use HTTPS and include
credentials; no cookie `Domain` configuration is required.

## Compatibility boundary

The schemas and statuses in this file reflect the current router/OpenAPI
implementation. OpenAPI does not describe the receipt body because that route
streams and validates raw bytes directly; this document is authoritative for
that upload. No pagination parameters exist on current `me` list endpoints.
