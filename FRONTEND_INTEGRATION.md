# directpilot-web Integration Guide

## Runtime configuration

Set the frontend's public API-origin environment variable to:

```dotenv
NEXT_PUBLIC_DIRECTPILOT_API_URL=https://api.directpilot.ir
```

If `directpilot-web` uses a framework other than Next.js, map this value into
that framework's public build-time variable. Keep one API client and do not add
`/api/v1` to the variable itself.

```ts
const API_URL = process.env.NEXT_PUBLIC_DIRECTPILOT_API_URL!;

async function api(path: string, init: RequestInit = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(init.body instanceof Blob ? {} : { "Content-Type": "application/json" }),
      ...init.headers,
    },
  });
  return response;
}
```

## Endpoint table

| Method | Endpoint | Auth | Success |
|---|---|---|---:|
| POST | `/api/v1/auth/register` | Public | 201 |
| POST | `/api/v1/auth/login` | Public | 200 |
| POST | `/api/v1/auth/logout` | Cookie | 200 |
| GET | `/api/v1/auth/me` | Cookie | 200 |
| GET | `/api/v1/plans` | Public | 200 |
| POST | `/api/v1/orders` | Cookie | 201 |
| GET | `/api/v1/orders/me` | Cookie | 200 |
| GET | `/api/v1/orders/{id}` | Cookie | 200 |
| POST | `/api/v1/payments/card-transfer` | Cookie | 201 |
| POST | `/api/v1/payments/{id}/receipt` | Cookie | 200 |
| GET | `/api/v1/payments/me` | Cookie | 200 |
| GET | `/api/v1/subscription/me` | Cookie | 200 |
| POST | `/api/v1/integrations/instagram/connect` | Cookie + entitlement | 200 |
| GET | `/api/v1/integrations/instagram/callback` | OAuth state | 200 |
| GET | `/api/v1/integrations/instagram/status` | Cookie | 200 |
| GET | `/api/v1/integrations/instagram/accounts` | Cookie | 200 |

## Authentication flow

The browser integration uses a Secure, HttpOnly, SameSite=Lax session cookie.
Every API call, including login, must set `credentials: "include"`. Do not save
the JSON `access_token`; it exists for non-browser Bearer clients and cannot be
made safer than the HttpOnly cookie in browser JavaScript.

At application startup:

1. call `GET /api/v1/auth/me`;
2. treat 200 as authenticated and retain the returned public principal in
   memory;
3. treat 401 as signed out.

Registration is a two-step flow: register, then login.

```ts
await api("/api/v1/auth/register", {
  method: "POST",
  body: JSON.stringify({
    email, password, display_name,
    tenant_name, tenant_slug,
    store_name, store_slug,
  }),
});
await api("/api/v1/auth/login", {
  method: "POST",
  body: JSON.stringify({ email, password }),
});
```

Logout:

```ts
await api("/api/v1/auth/logout", { method: "POST" });
```

Clear frontend user/query state after a successful logout. The server revokes
the session and expires its cookie.

## Error contract

Business and authentication errors:

```json
{"detail":{"code":"invalid_credentials","message":"Invalid credentials"}}
```

Use `detail.code` for decisions and `detail.message` for safe display. Request
shape errors use FastAPI's HTTP 422 list:

```json
{"detail":[{"type":"...","loc":["body","field"],"msg":"...","input":"..."}]}
```

At minimum handle 400, 401, 403, 404, 409, 413, 422, 502, and 503. A 401 from
an authenticated request should clear local principal/query state and lead to
login. Do not display raw provider responses.

## Plan → order → payment → subscription

1. Fetch `GET /api/v1/plans`; render backend price, currency, duration and limits.
2. Create an order with only `{"plan_public_id":"..."}`.
3. For a paid order, create card transfer with
   `{"order_public_id":"..."}`.
4. Display the returned payment `amount`, `currency`, bank/account/card fields,
   and transfer instructions. Do not use frontend-authored amounts.
5. Upload the receipt as raw bytes.
6. Poll/refetch `/api/v1/payments/me` and `/api/v1/subscription/me` after review.

Example order:

```ts
const orderResponse = await api("/api/v1/orders", {
  method: "POST",
  body: JSON.stringify({ plan_public_id: selectedPlan.public_id }),
});
const order = await orderResponse.json();
```

Example payment instructions:

```ts
const paymentResponse = await api("/api/v1/payments/card-transfer", {
  method: "POST",
  body: JSON.stringify({ order_public_id: order.public_id }),
});
const instructions = await paymentResponse.json();
// Render instructions.payment.amount; never recalculate it client-side.
```

### Receipt upload

Do not use `FormData`. Send the selected JPEG, PNG, or PDF `File` itself:

```ts
const response = await fetch(
  `${API_URL}/api/v1/payments/${paymentPublicId}/receipt`,
  {
    method: "POST",
    credentials: "include",
    headers: { Accept: "application/json", "Content-Type": file.type },
    body: file,
  },
);
```

The declared type must match the file signature. The default maximum is 5 MiB.
The receipt remains private; the customer API returns status and
`receipt_configured`, not a public file URL.

## Instagram OAuth flow

1. Check `GET /api/v1/integrations/instagram/status` to render entitlement,
   capacity, and current accounts.
2. Call `POST /api/v1/integrations/instagram/connect` with no body.
3. Navigate the user to the returned `authorization_url` before `expires_at`.
4. Meta returns to the API callback. The backend validates one-time state,
   exchanges the code, stores the encrypted token, and returns JSON.
5. Refetch `/status` or `/accounts` to obtain safe connection state.

Current callback behavior is a 200 JSON response at the API origin; it does not
redirect to a `directpilot.ir` page. If opening OAuth in a separate browsing
context, use status polling to observe completion. Never parse OAuth state or
handle Meta access tokens in the frontend.

Connect response:

```json
{"authorization_url":"https://www.instagram.com/oauth/authorize?...","expires_at":"2026-08-12T04:10:00Z"}
```

Status response:

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

## Required frontend state

The API requires only these frontend-owned states:

- authentication: unknown/loading, authenticated principal, or signed out;
- selected backend `plan_public_id`;
- current order/payment/subscription records returned by the API;
- Instagram entitlement/capacity/account status returned by the API;
- upload progress and normalized API error.

Do not store tenant/store internal IDs, plan prices, payment decisions, Meta
tokens, OAuth state, or session credentials in application state. The complete
schema reference and error-code table are in `API_CONTRACT_BACKEND.md`.
