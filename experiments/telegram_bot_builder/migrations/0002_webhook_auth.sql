-- DirectPilot TelBot UAT migration 0002: webhook authenticity/idempotency only.
-- Execute ONLY on Neon project curly-cell-93038441, UAT branch br-tiny-poetry-arz49v2o, DB telbot.
-- No production operation, no provider token or real customer data.
DO $$
BEGIN
  IF current_database() <> 'telbot'
     OR NOT EXISTS (SELECT 1 FROM telbot.schema_migrations WHERE version='0001_telbot_foundation')
     OR EXISTS (SELECT 1 FROM telbot.schema_migrations WHERE version='0002_webhook_auth')
  THEN
    RAISE EXCEPTION 'Invalid foundation or already applied; aborting TelBot UAT migration';
  END IF;
END $$;
ALTER TABLE telbot.bots
  ADD COLUMN webhook_secret_digest bytea,
  ADD CONSTRAINT webhook_secret_digest_len
      CHECK (webhook_secret_digest IS NULL OR octet_length(webhook_secret_digest)=32);
CREATE TABLE telbot.manager_inbound_updates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  telegram_update_id bigint NOT NULL UNIQUE CHECK (telegram_update_id >= 0),
  event_type varchar(40) NOT NULL CHECK (event_type IN ('managed_bot','other')),
  processing_status varchar(20) NOT NULL DEFAULT 'received'
    CHECK (processing_status IN ('received','processed','ignored','failed')),
  created_at timestamptz NOT NULL DEFAULT now(),
  processed_at timestamptz
);
INSERT INTO telbot.schema_migrations(version,description)
VALUES ('0002_webhook_auth','Separate manager update deduplication and SHA-256 child webhook secret digests');
