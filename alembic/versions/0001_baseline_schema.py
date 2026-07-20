"""Baseline of the schema that existed before Alembic was introduced."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001_baseline_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


TABLE_ORDER = (
    "customers",
    "faqs",
    "instagram_comment_events",
    "instagram_comment_public_replies",
    "instagram_events",
    "manychat_events",
    "module_definitions",
    "products",
    "stores",
    "telegram_events",
    "admin_audit_logs",
    "conversations",
    "instagram_media_products",
    "orders",
    "product_media_assets",
    "store_instagram_connections",
    "store_modules",
    "training_drafts",
    "knowledge_versions",
    "social_content_drafts",
    "instagram_publish_jobs",
    "knowledge_items",
    "product_categories",
    "catalog_products",
    "product_aliases",
)

INDEXES = {
    "customers": (("ix_customers_instagram_user_id", ("instagram_user_id",), True),),
    "instagram_comment_events": (
        ("ix_instagram_comment_events_comment_id", ("comment_id",), True),
        ("ix_instagram_comment_events_ig_account_id", ("ig_account_id",), False),
        ("ix_instagram_comment_events_media_id", ("media_id",), False),
        ("ix_instagram_comment_events_status", ("status",), False),
    ),
    "instagram_comment_public_replies": (
        ("ix_instagram_comment_public_replies_comment_id", ("comment_id",), True),
        ("ix_instagram_comment_public_replies_status", ("status",), False),
    ),
    "instagram_events": (
        ("ix_instagram_events_message_id", ("message_id",), True),
        ("ix_instagram_events_sender_id", ("sender_id",), False),
        ("ix_instagram_events_status", ("status",), False),
    ),
    "manychat_events": (
        ("ix_manychat_events_contact_id", ("contact_id",), False),
        ("ix_manychat_events_page_id", ("page_id",), False),
        ("ix_manychat_events_request_key", ("request_key",), True),
        ("ix_manychat_events_status", ("status",), False),
    ),
    "module_definitions": (
        ("ix_module_definitions_availability", ("availability",), False),
        ("ix_module_definitions_category", ("category",), False),
    ),
    "products": (("ix_products_name", ("name",), False),),
    "stores": (
        ("ix_stores_active_version_id", ("active_version_id",), False),
        ("ix_stores_slug", ("slug",), True),
        ("ix_stores_status", ("status",), False),
    ),
    "telegram_events": (
        ("ix_telegram_events_chat_id", ("chat_id",), False),
        ("ix_telegram_events_sender_id", ("sender_id",), False),
        ("ix_telegram_events_status", ("status",), False),
        ("ix_telegram_events_update_id", ("update_id",), True),
    ),
    "admin_audit_logs": (
        ("ix_admin_audit_logs_action", ("action",), False),
        ("ix_admin_audit_logs_entity_type", ("entity_type",), False),
        ("ix_admin_audit_logs_store_id", ("store_id",), False),
        ("ix_admin_audit_logs_timestamp", ("timestamp",), False),
    ),
    "conversations": (("ix_conversations_customer_id", ("customer_id",), False),),
    "instagram_media_products": (
        ("ix_instagram_media_products_media_id", ("media_id",), True),
        ("ix_instagram_media_products_product_id", ("product_id",), False),
    ),
    "orders": (
        ("ix_orders_customer_id", ("customer_id",), False),
        ("ix_orders_product_id", ("product_id",), False),
        ("ix_orders_status", ("status",), False),
    ),
    "product_media_assets": (
        ("ix_product_media_assets_product_id", ("product_id",), False),
        ("ix_product_media_assets_sha256", ("sha256",), False),
        ("ix_product_media_assets_status", ("status",), False),
        ("ix_product_media_assets_store_id", ("store_id",), False),
    ),
    "store_instagram_connections": (
        ("ix_store_instagram_connections_ig_user_id", ("ig_user_id",), True),
        ("ix_store_instagram_connections_status", ("status",), False),
        ("ix_store_instagram_connections_store_id", ("store_id",), True),
    ),
    "store_modules": (
        ("ix_store_modules_module_code", ("module_code",), False),
        ("ix_store_modules_status", ("status",), False),
        ("ix_store_modules_store_id", ("store_id",), False),
    ),
    "training_drafts": (
        ("ix_training_drafts_status", ("status",), False),
        ("ix_training_drafts_store_id", ("store_id",), False),
    ),
    "knowledge_versions": (
        ("ix_knowledge_versions_store_id", ("store_id",), False),
    ),
    "social_content_drafts": (
        ("ix_social_content_drafts_media_asset_id", ("media_asset_id",), False),
        ("ix_social_content_drafts_product_id", ("product_id",), False),
        ("ix_social_content_drafts_source_hash", ("source_hash",), False),
        ("ix_social_content_drafts_status", ("status",), False),
        ("ix_social_content_drafts_store_id", ("store_id",), False),
    ),
    "instagram_publish_jobs": (
        ("ix_instagram_publish_jobs_content_draft_id", ("content_draft_id",), False),
        ("ix_instagram_publish_jobs_status", ("status",), False),
        ("ix_instagram_publish_jobs_store_id", ("store_id",), False),
    ),
    "knowledge_items": (
        ("ix_knowledge_items_knowledge_version_id", ("knowledge_version_id",), False),
    ),
    "product_categories": (
        ("ix_product_categories_knowledge_version_id", ("knowledge_version_id",), False),
    ),
    "catalog_products": (
        ("ix_catalog_products_category_id", ("category_id",), False),
        ("ix_catalog_products_knowledge_version_id", ("knowledge_version_id",), False),
        ("ix_catalog_products_product_id", ("product_id",), False),
    ),
    "product_aliases": (
        ("ix_product_aliases_catalog_product_id", ("catalog_product_id",), False),
        ("ix_product_aliases_normalized_value", ("normalized_value",), False),
    ),
}


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("instagram_user_id", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "faqs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("question", sa.String(500), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("question"),
    )
    op.create_table(
        "instagram_comment_events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("comment_id", sa.String(100), nullable=False),
        sa.Column("ig_account_id", sa.String(100), nullable=False),
        sa.Column("media_id", sa.String(100), nullable=False),
        sa.Column("username", sa.String(200), nullable=True),
        sa.Column("comment_text", sa.Text(), nullable=False),
        sa.Column("media_product_type", sa.String(50), nullable=True),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("recipient_id", sa.String(100), nullable=True),
        sa.Column("response_message_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "instagram_comment_public_replies",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("comment_id", sa.String(100), nullable=False),
        sa.Column("reply_text", sa.Text(), nullable=False),
        sa.Column("reply_comment_id", sa.String(100), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "instagram_events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("message_id", sa.String(255), nullable=False),
        sa.Column("sender_id", sa.String(100), nullable=False),
        sa.Column("recipient_id", sa.String(100), nullable=False),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("response_message_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "manychat_events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("request_key", sa.String(64), nullable=False),
        sa.Column("page_id", sa.String(40), nullable=False),
        sa.Column("contact_id", sa.String(40), nullable=False),
        sa.Column("last_interaction", sa.DateTime(timezone=True), nullable=False),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "module_definitions",
        sa.Column("code", sa.String(60), primary_key=True, nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("short_description", sa.String(500), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("monthly_price", sa.Integer(), nullable=False),
        sa.Column("setup_price", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("dependencies", sa.JSON(), nullable=False),
        sa.Column("default_limits", sa.JSON(), nullable=False),
        sa.Column("availability", sa.String(20), nullable=False),
        sa.Column("is_sellable", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "stores",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("active_version_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "telegram_events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("update_id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.String(100), nullable=False),
        sa.Column("sender_id", sa.String(100), nullable=False),
        sa.Column("message_id", sa.String(100), nullable=False),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("response_message_id", sa.String(100), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=True),
        sa.Column("details_json", sa.JSON(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("store_id",), ("stores.id",)),
    )
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("user_message", sa.Text(), nullable=False),
        sa.Column("assistant_message", sa.Text(), nullable=True),
        sa.Column("needs_human", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("customer_id",), ("customers.id",)),
    )
    op.create_table(
        "instagram_media_products",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("media_id", sa.String(100), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("media_product_type", sa.String(50), nullable=True),
        sa.Column("permalink", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("product_id",), ("products.id",)),
    )
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("customer_id",), ("customers.id",)),
        sa.ForeignKeyConstraint(("product_id",), ("products.id",)),
    )
    op.create_table(
        "product_media_assets",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("product_id",), ("products.id",)),
        sa.ForeignKeyConstraint(("store_id",), ("stores.id",)),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_table(
        "store_instagram_connections",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("ig_user_id", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("token_ciphertext", sa.Text(), nullable=True),
        sa.Column("token_key_id", sa.String(100), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("store_id",), ("stores.id",)),
    )
    op.create_table(
        "store_modules",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("module_code", sa.String(60), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("custom_monthly_price", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("billing_interval", sa.String(20), nullable=False),
        sa.Column("limits_json", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("module_code",), ("module_definitions.code",)),
        sa.ForeignKeyConstraint(("store_id",), ("stores.id",)),
        sa.UniqueConstraint("store_id", "module_code", name="uq_store_module"),
    )
    op.create_table(
        "training_drafts",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("source_name", sa.String(255), nullable=True),
        sa.Column("source_payload", sa.Text(), nullable=True),
        sa.Column("draft_payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("store_id",), ("stores.id",)),
    )
    op.create_table(
        "knowledge_versions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("source_draft_id", sa.Integer(), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("source_draft_id",), ("training_drafts.id",)),
        sa.ForeignKeyConstraint(("store_id",), ("stores.id",)),
        sa.UniqueConstraint("source_draft_id"),
        sa.UniqueConstraint(
            "store_id",
            "version_number",
            name="uq_knowledge_versions_store_version",
        ),
    )
    op.create_table(
        "social_content_drafts",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("media_asset_id", sa.String(36), nullable=False),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("hashtags", sa.JSON(), nullable=False),
        sa.Column("alt_text", sa.String(1000), nullable=False),
        sa.Column("sales_keywords", sa.JSON(), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("media_asset_id",), ("product_media_assets.id",)),
        sa.ForeignKeyConstraint(("product_id",), ("products.id",)),
        sa.ForeignKeyConstraint(("store_id",), ("stores.id",)),
    )
    op.create_table(
        "instagram_publish_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("content_draft_id", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("meta_container_id", sa.String(100), nullable=True),
        sa.Column("meta_media_id", sa.String(100), nullable=True),
        sa.Column("permalink", sa.String(500), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("content_draft_id",), ("social_content_drafts.id",)),
        sa.ForeignKeyConstraint(("store_id",), ("stores.id",)),
        sa.UniqueConstraint(
            "content_draft_id", name="uq_instagram_publish_job_draft"
        ),
        sa.UniqueConstraint(
            "idempotency_key", name="uq_instagram_publish_job_key"
        ),
    )
    op.create_table(
        "knowledge_items",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("knowledge_version_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("normalized_title", sa.String(500), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("keywords", sa.JSON(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(("knowledge_version_id",), ("knowledge_versions.id",)),
        sa.UniqueConstraint(
            "knowledge_version_id",
            "kind",
            "title",
            name="uq_knowledge_items_version_kind_title",
        ),
    )
    op.create_table(
        "product_categories",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("knowledge_version_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("normalized_name", sa.String(200), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(("knowledge_version_id",), ("knowledge_versions.id",)),
        sa.UniqueConstraint(
            "knowledge_version_id",
            "normalized_name",
            name="uq_product_categories_version_normalized_name",
        ),
    )
    op.create_table(
        "catalog_products",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("knowledge_version_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("external_key", sa.String(200), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(("category_id",), ("product_categories.id",)),
        sa.ForeignKeyConstraint(("knowledge_version_id",), ("knowledge_versions.id",)),
        sa.ForeignKeyConstraint(("product_id",), ("products.id",)),
        sa.UniqueConstraint(
            "knowledge_version_id",
            "external_key",
            name="uq_catalog_products_version_external_key",
        ),
        sa.UniqueConstraint(
            "knowledge_version_id",
            "product_id",
            name="uq_catalog_products_version_product",
        ),
    )
    op.create_table(
        "product_aliases",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("catalog_product_id", sa.Integer(), nullable=False),
        sa.Column("value", sa.String(200), nullable=False),
        sa.Column("normalized_value", sa.String(200), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(("catalog_product_id",), ("catalog_products.id",)),
        sa.UniqueConstraint(
            "catalog_product_id",
            "normalized_value",
            name="uq_product_aliases_product_normalized",
        ),
    )
    for table_name in TABLE_ORDER:
        for index_name, columns, unique in INDEXES.get(table_name, ()):
            op.create_index(index_name, table_name, list(columns), unique=unique)


def downgrade() -> None:
    for table_name in reversed(TABLE_ORDER):
        for index_name, _columns, _unique in reversed(INDEXES.get(table_name, ())):
            op.drop_index(index_name, table_name=table_name)
        op.drop_table(table_name)
