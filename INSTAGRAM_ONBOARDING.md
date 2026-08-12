# Official Instagram Customer Onboarding

DirectPilot implements **Instagram API with Instagram Login**. A Facebook Page
is not required by this path. Customers never provide an Instagram password.

## Configuration

Configure the Meta app for Instagram messaging/content management and register
the exact HTTPS redirect URI:
`https://api.directpilot.ir/api/v1/integrations/instagram/callback`.

Required scopes:

- `instagram_business_basic`
- `instagram_business_manage_messages`
- `instagram_business_manage_comments`

Runtime settings include `META_APP_ID`, `META_APP_SECRET`,
`META_OAUTH_REDIRECT_URI`, the official authorize/token URLs and the existing
Fernet `INSTAGRAM_TOKEN_ENCRYPTION_KEY`.

## Security flow

1. Authenticated customer with active Instagram capacity requests connect.
2. Backend creates 256-bit URL-safe state and persists only its SHA-256 digest,
   tenant/store/user binding and a short expiry.
3. Meta redirects a code and state to the backend.
4. Backend consumes state exactly once before exchanging the code.
5. Provider adapter exchanges for a long-lived token and reads the Professional
   account identifier/username.
6. Token is Fernet-encrypted into the existing store `InstagramConnection`.
7. Frontend receives only public connection/account status.

Webhook setup continues to use
`/api/v1/integrations/instagram/webhook` on the restricted gateway. Signature
verification and the global outbound kill switch remain unchanged.
