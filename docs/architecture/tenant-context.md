# TenantContext Resolution Contract

## Purpose

TenantContext is an immutable, credential-free description of the store boundary established at a trusted request or service boundary. It is the foundation for future tenant-filtered reads and writes, user memberships, connector credentials and audit correlation.

This foundation does not make the current MVP multi-tenant. Existing product, customer, conversation and order behavior is unchanged, and current routes are not globally rewired in FOUNDATION-01.

## Contract

TenantContext is a frozen dataclass containing:

| Field | Meaning |
|---|---|
| store_id | Internal Store primary key. |
| store_slug | Canonical store slug. |
| store_status | Current lifecycle status retained for policy decisions. |
| resolution_source | Typed source: subdomain, connector, session, explicit_internal or development_default. |
| actor | Frozen typed metadata: ID, actor type and optional role. |
| membership_id | Future membership reference; currently null. |
| connector | Frozen connector type, connection ID and provider account ID. |
| correlation_id | Always-present request/operation identifier. |
| is_default_fallback | Explicit marker for permitted development fallback. |

Actor types are user, connector, system and anonymous. Connector types currently describe Instagram, Telegram and ManyChat. The safe serialization method returns primitive structured-log fields only. The context stores no ORM session, request object, token, secret or credential.

## Trusted resolution sources

### Host or subdomain

resolve_tenant_from_host accepts only a host and configured base domain. A valid tenant subdomain resolves to an existing permitted Store. resolve_tenant_from_request deliberately reads only Host and the defined correlation header; query parameters, request bodies and tenant-like headers are not tenant authority.

### Instagram connector

resolve_instagram_tenant maps an Instagram account ID through StoreInstagramConnection. The mapping must be unique, the connection active and the Store not disabled, suspended or deleted. Unknown, inactive and ambiguous mappings fail without business writes or network calls.

### Explicit internal

resolve_explicit_internal_tenant requires trusted=True. This flag is for a call site already established as internal; it must never be populated directly from an HTTP field. The Store must still exist and be permitted.

### Development default

In development, canonical localhost hosts may resolve to the default Store. The resulting context uses development_default and is_default_fallback=true. Instagram’s legacy configured-account fallback is available only when the caller explicitly enables it and the environment is development.

### Future session

resolve_session_tenant is intentionally unavailable and raises a typed domain error. It never falls back to the default Store. A later authentication task will replace it with membership-backed resolution.

## Production fail-closed rules

- Localhost and an unknown or malformed host do not resolve.
- Unknown, inactive or ambiguous connector mappings do not resolve.
- Deleted, disabled and suspended Stores do not produce a context.
- A global Instagram account setting cannot provide production fallback.
- Client body, query and arbitrary header values cannot select or override a Store.
- Resolution performs no business write and no provider network request.

Domain errors distinguish unknown tenant, inactive tenant, unknown connector, ambiguous mapping, invalid host, untrusted explicit selection and unavailable session resolution. tenant_resolution_http_exception maps these to safe responses. Public unknown/inactive/ambiguous errors use the same generic 404 message so hidden Store existence is not disclosed.

## Correlation IDs

The only accepted incoming header is X-Correlation-ID. Values are trimmed, limited to 128 characters and restricted to letters, digits, dot, underscore, colon and hyphen. Control characters, newlines, spaces, oversized or malformed values are replaced with a generated UUID. No global mutable state or database persistence is used.

## Safe usage

Safe route boundary:

    context = resolve_tenant_from_request(request, db, settings)
    service.list_orders(context=context, db=db)

Safe connector boundary:

    context = resolve_instagram_tenant(db, recipient_account_id, settings)

Safe logging:

    logger.info("tenant_resolved", extra=context.to_safe_dict())

Unsafe patterns:

    # Never trust a client-selected tenant.
    store_slug = request.query_params["store_slug"]

    # Never treat entitlement as user authorization.
    if module_enabled(db, store, "sales_agent_core"):
        allow_admin_operation()

    # Never add credentials to TenantContext.
    context.meta_access_token = token

## Compatibility and future integration

parse_tenant_slug, store_by_slug and tenant_store_from_request remain available for the existing MVP. store_for_instagram_account, ensure_default_store and module_enabled are unchanged. New code should prefer the domain resolvers, while route migration must occur incrementally after schema ownership and authentication decisions.

Future tasks should pass TenantContext through the service layer, add tenant-aware writes and reads, implement User/StoreMembership session resolution, migrate connector credentials per Store, attach actor/correlation metadata to audit logs and finally disable legacy production fallbacks.
