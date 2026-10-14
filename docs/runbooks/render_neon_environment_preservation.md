# Render → Neon Production: Environment Variables — Preservation and Cutover Audit

**Date 2026-10-14. Status: SOURCE-INVENTORY PENDING / LIVE CUTOVER NOT AUTHORIZED.**

## Architecture: do not copy Render app secrets into Neon

Current Production is **Render web service** `directpilot-api`, service ID `srv-db0f3uc9v7es73b5k51g`, `autoDeploy=no`. Render still hosts the running Python FastAPI application. The independent Neon project `billowing-poetry-05589994` hosts **PostgreSQL only**; platform Functions are not available for this Neon project. Neon Postgres settings and roles are *not* a general-purpose Environment Variables repository.

**No Render application environment values should be copied to Neon Postgres.** The only anticipated runtime config change during a separately authorized, data-verified live cutover is updating the Render Production Backend database connection selector (`DATABASE_URL` or securely referenced `DATABASE_URL_FILE`) to the **new final Neon DB**, not the existing stale `neondb` rehearsal. Preserve all other original Render service keys and values. Protect `APPLICATION_SECRET`, `INSTAGRAM_TOKEN_ENCRYPTION_KEY` and other encryption/signing materials so restored tokens, existing login sessions and financial records remain readable. Do NOT insert secrets into database tables, connection options, project settings, Neon SQL functions, GitHub, chat or logs.

### Where keys belong

| Category (names only) | Authoritative location | Cutover policy |
| --- | --- | --- |
| `APP_ENV`, `APPLICATION_SECRET`, `SESSION_COOKIE_*`, `TRUSTED_HOSTS`, `CORS_ALLOWED_ORIGINS` | Render Production Web Service environment | **KEEP identical** (preserve session signing/cookie behavior) |
| `META_*`, `INSTAGRAM_TOKEN_ENCRYPTION_KEY`, `MEDIA_SIGNING_SECRET` | Render Production Web Service environment or existing secure file secret | **KEEP identical**; don't reconfigure Meta callbacks for DB-only move |
| `PAYEXA_*`, `KPAY_*`, `CARD_TRANSFER_*`, receipt storage settings | Render Production Web Service environment | **KEEP identical**; verify external legacy receipt files separately |
| `OPENAI_*`, `GROQ_*`, `OLLAMA_*`, `TELEGRAM_*` and other integrations | Render Production Web Service | **KEEP identical**, no provider access during database preparation |
| `DIRECTPILOT_*_ON_START` one-shot seed/bootstrap/password reset/payment flags | Render Production Web Service | Review privately, confirm unintended one-shot writers OFF before deployment; **never toggle without specific approval** |
| `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`, `WEB_CONCURRENCY` and timeout settings | Render Production Web Service | **KEEP unchanged** until controlled load test/review; don't assume a new value is safe |
| `DATABASE_URL` / `DATABASE_URL_FILE` | Render Production Web Service | **ONLY final future planned change**, using verified separate *fresh* Neon database after approved freeze, backup, restore and parity. Currently unchanged |
| Database roles, databases, compute, TLS | Neon Production project | Manage ONLY DB-specific objects/settings when separately approved; not a place for API secrets |

## Current access constraints

- Connected Render `get_service` returns service metadata and an `environmentId`, **not environment keys or values**; no read/list-environment action is available in the connected Render tool.
- Render update_environment_variables supports **writing** keys to Render; no secure direct copy action exists to Neon and no new write is appropriate at this stage.
- Neon Functions returned `platform functions not available for this project`. It would be incorrect to claim Render variables have been moved, or to create a new Neon Function as a destination.
- Source Render database remains AVAILABLE, `ipAllowList=[]`; Neon `neondb` is the old restored snapshot, **not** a synchronized live target.

## Operator-only, secret-free key inventory

In a trusted local terminal or Render dashboard, record a file containing **ONLY environment variable names, one per line** for Production Backend, e.g.:

```text
APP_ENV
DATABASE_URL
APPLICATION_SECRET
META_APP_SECRET
INSTAGRAM_TOKEN_ENCRYPTION_KEY
PAYEXA_API_KEY
```

Those are example names, **not** a claim all exist in the service. Do NOT export `KEY=value`, do NOT save credentials, secrets, session cookies, URI values, or customer data. Store private name-only files outside the Git repository.

Prepare a SECOND names-only file for the *proposed future Render environment*, preserving **all current names**. No actual values are needed for this check. On the trusted laptop (Python 3.10+):

```powershell
python -m tools.render_env_key_audit --render-keys "D:\\private\\render_prod_keys.txt" --proposed-render-keys "D:\\private\\render_cutover_keys.txt"
```

It **must** report `ENV_KEY_PRESERVATION: PASS_NAMES_ONLY` and `MISSING_KEY_NAMES: NONE`. Any removed existing key is a hard stop. This does **not** check secret VALUE parity, runtime behavior, actual Render inventory, or `DATABASE_URL` host contents; private comparison with current Render dashboard and a separate DB-target validation are still required. Do not paste a secret or `KEY=value` to this tool; it rejects malformed names.

## Ready-before-cutover variable-change checklist

1. Capture current Production Render service ID, environment ID and deployment commit; verify autoDeploy stays disabled.
2. With approved private Render access, inventory current key names and confirm value continuity through a secure, non-printing operator process. Avoid long-lived plaintext exports of all secret values.
3. Confirm application signing/encryption keys persist exactly; Meta callback base URL and existing bank-card/payments remain unchanged.
4. Evaluate source database write freeze and durable Meta/Payexa webhook hold/replay BEFORE deciding on final database operation. Don't merely display a frontend maintenance banner.
5. Verify the separately approved **new empty Neon final DB** identity and its restore with latest write-frozen Render backup; full table/critical-business parity and rollback must PASS.
6. Securely stage ONLY the Neon final DB URL for a controlled Render backend change; don't reference rehearsal `neondb`. Validate TLS and expected host/database privately without printing credentials.
7. During a separately approved go/no-go window, update only the DB selector on Render and monitor. No automatic copy of other env vars to Neon. Do not start if other Render values would be deleted/overwritten.

**Current action status:** Offline key-preservation checker prepared; current Render environment keys are **not yet obtainable from connected tools**, no private operator inventory provided, no values copied or modified, no Production/UAT deploy or Cutover performed. See `docs/runbooks/neon_free_usage_and_maintenance_plan.md` for remaining safeguards.
