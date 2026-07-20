# AUDIT-01 — Route Inventory

`app/main.py::app` exposes all rows below, including FastAPI-generated docs and the static mount. `app/public_instagram_gateway.py::app` exposes only Instagram webhook GET/POST, `/privacy`, `/data-deletion`, and signed `/media/publish/{asset_id}`; it disables docs/OpenAPI.

| Method | Path | Source / handler | Current authentication or validation | Category |
|---|---|---|---|---|
| GET | `/` | `app/main.py::home` | None; redirects to `/demo` | public page |
| GET | `/demo` | `app/main.py::demo` | None | public page |
| GET | `/health` | `app/main.py::health` | None | internal/test |
| GET | `/products` | `app/main.py::list_products` | Pydantic response only; no auth | store operation |
| GET | `/faqs` | `app/main.py::list_faqs` | No auth | store operation |
| GET | `/leads` | `app/main.py::list_leads` | No auth | store operation |
| GET | `/orders` | `app/main.py::list_orders` | No auth | store operation |
| POST | `/chat` | `app/main.py::chat` | `ChatRequest`; no auth | store operation |
| GET/HEAD | `/static/{path}` | `app/main.py` — `StaticFiles` mount | Framework path handling; no auth | public page |
| GET | `/openapi.json` | `app/main.py::app` FastAPI-generated OpenAPI handler | No auth; absent on public gateway | internal/test |
| GET | `/docs` | `app/main.py::app` FastAPI-generated Swagger UI handler | No auth; absent on public gateway | internal/test |
| GET | `/docs/oauth2-redirect` | `app/main.py::app` FastAPI-generated redirect handler | No auth; absent on public gateway | internal/test |
| GET | `/redoc` | `app/main.py::app` FastAPI-generated ReDoc handler | No auth; absent on public gateway | internal/test |
| GET | `/admin` | `app/admin.py::admin_page` | `require_admin_read`: development + loopback client/local host | admin |
| GET | `/admin/api/state` | `app/admin.py::admin_state` | Local read guard | admin |
| POST | `/admin/api/drafts/analyze` | `app/admin.py::analyze_draft` | Local mutation guard + same origin/fetch-site + schema | admin |
| PUT | `/admin/api/drafts/{draft_id}` | `app/admin.py::update_draft` | Same local mutation guard + schema | admin |
| POST | `/admin/api/drafts/{draft_id}/publish` | `app/admin.py::publish_draft` | Same local mutation guard; publish validation | admin |
| POST | `/admin/api/test` | `app/admin.py::test_agent` | Same local mutation guard + schema | admin |
| GET | `/admin/api/content-studio` | `app/admin_content.py::content_studio_state` | Local read guard | admin |
| POST | `/admin/api/products/{product_id}/media` | `app/admin_content.py::upload_product_media` | Local mutation; content module; JPEG/count/schema validation | admin |
| GET | `/admin/api/product-media/{asset_id}/preview` | `app/admin_content.py::preview_product_media` | Local read; content module | admin |
| DELETE | `/admin/api/product-media/{asset_id}` | `app/admin_content.py::remove_product_media` | Local mutation; content module/reference check | admin |
| POST | `/admin/api/content-drafts/generate` | `app/admin_content.py::generate_content` | Local mutation; content strategy module + schema | admin |
| PUT | `/admin/api/content-drafts/{draft_id}` | `app/admin_content.py::edit_content` | Local mutation; review module + revision/schema | admin |
| POST | `/admin/api/content-drafts/{draft_id}/approve` | `app/admin_content.py::approve_content` | Local mutation; review module + revision | admin |
| POST | `/admin/api/content-drafts/{draft_id}/publish` | `app/admin_content.py::publish_content` | Local mutation; review/publish modules, revision/readiness | admin |
| GET | `/admin/api/module-marketplace` | `app/admin_modules.py::module_marketplace` | Local read; validated `store_slug` query | admin |
| GET | `/admin/api/provider/stores` | `app/admin_modules.py::provider_stores` | Local read | admin |
| POST | `/admin/api/provider/stores` | `app/admin_modules.py::create_provider_store` | Local mutation + store schema/slug checks | admin |
| PATCH | `/admin/api/provider/stores/{store_slug}/modules/{module_code}` | `app/admin_modules.py::update_store_module` | Local mutation + entitlement/dependency checks | admin |
| PATCH | `/admin/api/provider/module-catalog/{module_code}` | `app/admin_modules.py::update_catalog_price` | Local mutation + price schema | admin |
| GET | `/instagram/status` | `app/instagram.py::instagram_status` | No auth; returns readiness booleans, not secrets | internal/test |
| GET | `/webhooks/instagram` | `app/instagram.py::verify_instagram_webhook` | Meta mode/token challenge comparison | public webhook |
| POST | `/webhooks/instagram` | `app/instagram.py::receive_instagram_webhook` | Optional-by-setting HMAC-SHA256 signature + JSON parsing | public webhook |
| GET | `/instagram/setup` | `app/instagram_setup.py::instagram_setup_page` | Development + loopback/local host; issues nonce cookie | setup |
| POST | `/instagram/setup` | `app/instagram_setup.py::save_instagram_setup` | Local guard, same origin/fetch-site, one-use cookie nonce, formats | setup |
| POST | `/instagram/setup/verify-token` | `app/instagram_setup.py::rotate_instagram_verify_token` | Same local/origin/nonce controls + token format | setup |
| GET | `/privacy` | `app/legal.py::privacy_policy` | None | public page |
| GET | `/data-deletion` | `app/legal.py::data_deletion` | None | public page |
| POST | `/integrations/manychat/instagram` | `app/manychat.py::receive_manychat_instagram` | Configured bearer secret + Pydantic payload + deduplication | public webhook |
| GET | `/media/publish/{asset_id}` | `app/public_media.py::public_product_image` | Expiry and HMAC signature; ready asset required | public page |
| GET | `/telegram/status` | `app/telegram.py::telegram_status` | No auth; readiness booleans only | internal/test |
| POST | `/webhooks/telegram` | `app/telegram.py::receive_telegram_webhook` | Telegram secret header + JSON object validation | public webhook |
| GET | `/telegram/setup` | `app/telegram_setup.py::telegram_setup_page` | Development + loopback/local host; issues nonce | setup |
| POST | `/telegram/setup` | `app/telegram_setup.py::save_telegram_setup` | Local/origin/fetch-site, matching one-use cookie/body nonce, token format; may call `getMe` | setup |

## Route evidence notes

- Admin “authentication” is a development/loopback boundary (`app/admin.py::require_local_admin()`), not a user identity system.
- Module gates are feature validation in addition to local admin guards; they are not user authentication.
- Instagram POST signature checking can be disabled by `META_SIGNATURE_REQUIRED`; the table records current code behavior, not a security assessment.
- **Needs Verification:** intended exposure of `/instagram/status` and `/telegram/status` in any future non-local deployment is not documented.
