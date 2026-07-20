# AUDIT-01 — Database Model Inventory

**Database evidence:** `app/database.py` defines synchronous SQLAlchemy `engine`, `SessionLocal`, `Base`, and `get_db()`. `app/main.py::lifespan()` and `app/public_instagram_gateway.py::lifespan()` call `Base.metadata.create_all()`. Default configuration is SQLite. All current ORM models are in `app/models.py`.

| Model / table | Source and symbol | PK | Important foreign keys | `store_id` | Likely ownership | Current behavior |
|---|---|---|---|---|---|---|
| `Product` / `products` | `app/models.py::Product` | `id` | — | No | global | Legacy product truth used by demo, orders, catalog mappings, media, and replies. |
| `FAQ` / `faqs` | `app/models.py::FAQ` | `id` | — | No | global | Legacy active FAQ question/answer store. |
| `Customer` / `customers` | `app/models.py::Customer` | `id` | — | No | customer-owned | Customer channel identifier, optional name/phone; identifier is globally unique. |
| `Conversation` / `conversations` | `app/models.py::Conversation` | `id` | `customer_id → customers.id` | No | customer-owned | Persists user/assistant text, channel, and `needs_human`. |
| `Order` / `orders` | `app/models.py::Order` | `id` | `customer_id`, `product_id` | No | customer-owned | Pending order with quantity and floating-point unit price. |
| `InstagramEvent` / `instagram_events` | `app/models.py::InstagramEvent` | `id` | — | No | connector-owned | Deduplication/status record for Instagram DM text messages. |
| `InstagramMediaProduct` / `instagram_media_products` | `app/models.py::InstagramMediaProduct` | `id` | `product_id → products.id` | No | connector-owned | Maps a published Meta media ID to a product for comment replies. |
| `InstagramCommentEvent` / `instagram_comment_events` | `app/models.py::InstagramCommentEvent` | `id` | — | No | connector-owned | Deduplicates and records comment processing/reply status. |
| `InstagramCommentPublicReply` / `instagram_comment_public_replies` | `app/models.py::InstagramCommentPublicReply` | `id` | — | No | connector-owned | Ensures one tracked public acknowledgement per comment. |
| `TelegramEvent` / `telegram_events` | `app/models.py::TelegramEvent` | `id` | — | No | connector-owned | Deduplicates Telegram update IDs and stores reply status. |
| `ManyChatEvent` / `manychat_events` | `app/models.py::ManyChatEvent` | `id` | — | No | connector-owned | Deduplicates a hashed ManyChat request and caches its reply. |
| `Store` / `stores` | `app/models.py::Store` | `id` | `active_version_id` is an integer pointer, not declared FK | No | global | Store identity/lifecycle and active knowledge-version pointer. |
| `TrainingDraft` / `training_drafts` | `app/models.py::TrainingDraft` | `id` | `store_id → stores.id` | Yes | store-owned | Source/draft JSON and review/publish status for catalog training. |
| `KnowledgeVersion` / `knowledge_versions` | `app/models.py::KnowledgeVersion` | `id` | `store_id`, `source_draft_id` | Yes | store-owned | Immutable-numbered published knowledge version per store. |
| `ProductCategory` / `product_categories` | `app/models.py::ProductCategory` | `id` | `knowledge_version_id` | No; indirect | store-owned | Version-scoped normalized category. |
| `CatalogProduct` / `catalog_products` | `app/models.py::CatalogProduct` | `id` | `knowledge_version_id`, `product_id`, optional `category_id` | No; indirect | store-owned | Version-specific product snapshot linked to legacy `Product`. |
| `ProductAlias` / `product_aliases` | `app/models.py::ProductAlias` | `id` | `catalog_product_id` | No; indirect | store-owned | Normalized canonical/generated/manual product phrases. |
| `KnowledgeItem` / `knowledge_items` | `app/models.py::KnowledgeItem` | `id` | `knowledge_version_id` | No; indirect | store-owned | Versioned FAQ/rule answer with keywords and priority. |
| `AdminAuditLog` / `admin_audit_logs` | `app/models.py::AdminAuditLog` | `id` | `store_id` | Yes | audit/operational | Store action/entity/details JSON audit record. |
| `ProductMediaAsset` / `product_media_assets` | `app/models.py::ProductMediaAsset` | UUID string `id` | `store_id`, `product_id` | Yes | store-owned | Metadata and local storage key for validated JPEG product images. |
| `SocialContentDraft` / `social_content_drafts` | `app/models.py::SocialContentDraft` | `id` | `store_id`, `product_id`, `media_asset_id` | Yes | store-owned | Generated/reviewed caption, hashtags, alt text, keywords, and revision status. |
| `InstagramPublishJob` / `instagram_publish_jobs` | `app/models.py::InstagramPublishJob` | `id` | `store_id`, `content_draft_id` | Yes | audit/operational | Idempotent Meta container/publish status and identifiers. |
| `ModuleDefinition` / `module_definitions` | `app/models.py::ModuleDefinition` | `code` | — | No | global | Provider-owned module catalog, pricing, dependencies, limits, availability. |
| `StoreModule` / `store_modules` | `app/models.py::StoreModule` | `id` | `store_id`, `module_code` | Yes | store-owned | Store entitlement/status/trial/pricing/limits/config for one module. |
| `StoreInstagramConnection` / `store_instagram_connections` | `app/models.py::StoreInstagramConnection` | `id` | `store_id` | Yes | connector-owned | One active Instagram account mapping per store; optional token metadata columns. |

## Ownership notes

- `ProductCategory`, `CatalogProduct`, `ProductAlias`, and `KnowledgeItem` are store-owned only through the `KnowledgeVersion → Store` chain.
- No separate `Lead` table exists: `app/main.py::list_leads()` returns `Customer` rows whose `phone` is not null using `app/schemas.py::LeadRead`.
- The current customer/conversation/order and connector-event tables have no `store_id`; this is inventory evidence only, not a migration proposal.
- **Needs Verification:** whether `Store.active_version_id` deliberately remains an unconstrained pointer or is temporary MVP design is not documented in the model.

