-- Isolated TelBot UAT ONLY. Forward-only; legacy builder/configurations preserved.
DO $$ BEGIN
 IF current_database()<>'telbot' OR NOT EXISTS (SELECT 1 FROM telbot.schema_migrations WHERE version='0003_rule_api_calls')
 OR EXISTS (SELECT 1 FROM telbot.schema_migrations WHERE version='0004_showcase_inquiries') THEN
 RAISE EXCEPTION 'Invalid showcase migration target/version'; END IF;
END $$;
CREATE TABLE telbot.showcase_settings (
 tenant_id uuid NOT NULL, bot_id uuid PRIMARY KEY, enabled boolean NOT NULL DEFAULT false,
 updated_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY (tenant_id,bot_id) REFERENCES telbot.bots(tenant_id,id) ON DELETE RESTRICT
);
CREATE TABLE telbot.showcase_sessions (
 tenant_id uuid NOT NULL, bot_id uuid NOT NULL, telegram_user_id bigint NOT NULL CHECK (telegram_user_id>0),
 state_ciphertext bytea NOT NULL, last_update_id bigint NOT NULL DEFAULT -1,
 updated_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (bot_id,telegram_user_id),
 FOREIGN KEY (tenant_id,bot_id) REFERENCES telbot.bots(tenant_id,id) ON DELETE RESTRICT
);
CREATE TABLE telbot.showcase_inquiries (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL, bot_id uuid NOT NULL,
 telegram_user_id bigint NOT NULL CHECK (telegram_user_id>0), source_update_id uuid NOT NULL,
 industry varchar(40) NOT NULL, payload_ciphertext bytea NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE (bot_id,source_update_id),
 UNIQUE (tenant_id,bot_id,id),
 FOREIGN KEY (tenant_id,bot_id) REFERENCES telbot.bots(tenant_id,id) ON DELETE RESTRICT,
 FOREIGN KEY (tenant_id,bot_id,source_update_id) REFERENCES telbot.inbound_updates(tenant_id,bot_id,id) ON DELETE RESTRICT
);
CREATE INDEX showcase_inquiries_recent ON telbot.showcase_inquiries(tenant_id,bot_id,created_at DESC);
CREATE TABLE telbot.showcase_deliveries (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL, bot_id uuid NOT NULL,
 source_update_id uuid NOT NULL, kind varchar(16) NOT NULL CHECK (kind IN ('customer','owner')),
 payload_ciphertext bytea NOT NULL, status varchar(20) NOT NULL DEFAULT 'unknown' CHECK (status IN ('unknown','sent','rejected')),
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE (bot_id,source_update_id,kind),
 FOREIGN KEY (tenant_id,bot_id,source_update_id) REFERENCES telbot.inbound_updates(tenant_id,bot_id,id) ON DELETE RESTRICT
);
INSERT INTO telbot.schema_migrations(version,description) VALUES ('0004_showcase_inquiries','Own portfolio bot, encrypted scoped inquiry sessions and durable notification attempts');
