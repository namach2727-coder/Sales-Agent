-- DirectPilot TelBot / 0001_telbot_foundation.sql
-- APPLY TO: Neon project curly-cell-93038441, branch br-tiny-poetry-arz49v2o (uat), database telbot ONLY.
-- Never execute on production branch br-fancy-feather-arydwgj7 without separately approved release.
-- One transactional migration, no customer data, no secrets. Required role: database schema owner.
-- Keep statements split on the marker for tool-based single-transaction execution.

-- @@statement 1
DO $$ BEGIN IF current_database() <> 'telbot' THEN RAISE EXCEPTION 'Refusing to create TelBot schema outside telbot database'; END IF; END $$;

-- @@statement 2
CREATE SCHEMA IF NOT EXISTS telbot;

-- @@statement 3
CREATE TABLE telbot.schema_migrations (
  version varchar(32) PRIMARY KEY,
  description varchar(255) NOT NULL,
  applied_at timestamptz NOT NULL DEFAULT now()
);

-- @@statement 4
CREATE TABLE telbot.tenants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  display_name varchar(120) NOT NULL CHECK (length(btrim(display_name)) > 0),
  status varchar(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended','closed')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- @@statement 5
CREATE TABLE telbot.tenant_users (
  tenant_id uuid NOT NULL REFERENCES telbot.tenants(id) ON DELETE RESTRICT,
  telegram_user_id bigint NOT NULL CHECK (telegram_user_id > 0),
  role varchar(20) NOT NULL DEFAULT 'owner' CHECK (role IN ('owner','editor','viewer')),
  status varchar(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','revoked')),
  added_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, telegram_user_id)
);

-- @@statement 6
CREATE TABLE telbot.managed_bot_requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  request_id integer NOT NULL,
  owner_telegram_user_id bigint NOT NULL,
  status varchar(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','fulfilled','expired','cancelled')),
  requested_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  fulfilled_at timestamptz,
  UNIQUE (tenant_id,id),
  UNIQUE (tenant_id, request_id),
  FOREIGN KEY (tenant_id,owner_telegram_user_id) REFERENCES telbot.tenant_users(tenant_id,telegram_user_id) ON DELETE RESTRICT,
  CHECK (expires_at > requested_at),
  CHECK (status <> 'fulfilled' OR fulfilled_at IS NOT NULL)
);

-- @@statement 7
CREATE TABLE telbot.bots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES telbot.tenants(id) ON DELETE RESTRICT,
  telegram_bot_id bigint NOT NULL UNIQUE CHECK (telegram_bot_id > 0),
  username varchar(64),
  display_name varchar(120) NOT NULL CHECK (length(btrim(display_name)) > 0),
  owner_telegram_user_id bigint NOT NULL,
  managed_request_id uuid,
  credential_ciphertext bytea,
  credential_key_version smallint,
  status varchar(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','active','paused','revoked')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id,id),
  FOREIGN KEY (tenant_id,owner_telegram_user_id) REFERENCES telbot.tenant_users(tenant_id,telegram_user_id) ON DELETE RESTRICT,
  FOREIGN KEY (tenant_id,managed_request_id) REFERENCES telbot.managed_bot_requests(tenant_id,id) ON DELETE RESTRICT,
  CHECK ((credential_ciphertext IS NULL) = (credential_key_version IS NULL)),
  CHECK (credential_key_version IS NULL OR credential_key_version > 0),
  CHECK (status <> 'active' OR credential_ciphertext IS NOT NULL)
);

-- @@statement 8
CREATE TABLE telbot.configuration_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  bot_id uuid NOT NULL,
  version integer NOT NULL CHECK (version > 0),
  state varchar(20) NOT NULL DEFAULT 'draft' CHECK (state IN ('draft','published','archived')),
  greeting varchar(4096) NOT NULL CHECK (length(btrim(greeting)) > 0),
  fallback_reply varchar(4096) NOT NULL CHECK (length(btrim(fallback_reply)) > 0),
  created_by_telegram_user_id bigint NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  published_at timestamptz,
  UNIQUE (tenant_id,id),
  UNIQUE (bot_id,version),
  FOREIGN KEY (tenant_id,bot_id) REFERENCES telbot.bots(tenant_id,id) ON DELETE RESTRICT,
  FOREIGN KEY (tenant_id,created_by_telegram_user_id) REFERENCES telbot.tenant_users(tenant_id,telegram_user_id) ON DELETE RESTRICT,
  CHECK (state <> 'published' OR published_at IS NOT NULL)
);

-- @@statement 9
CREATE UNIQUE INDEX configuration_one_published_per_bot ON telbot.configuration_versions(bot_id) WHERE state='published';

-- @@statement 10
CREATE TABLE telbot.menu_buttons (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  configuration_id uuid NOT NULL,
  label varchar(64) NOT NULL CHECK (length(btrim(label)) > 0),
  action_type varchar(20) NOT NULL CHECK (action_type IN ('reply','url','callback')),
  action_value varchar(2048) NOT NULL CHECK (length(btrim(action_value)) > 0),
  sort_order smallint NOT NULL DEFAULT 0 CHECK (sort_order >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (configuration_id,sort_order),
  FOREIGN KEY (tenant_id,configuration_id) REFERENCES telbot.configuration_versions(tenant_id,id) ON DELETE CASCADE
);

-- @@statement 11
CREATE TABLE telbot.reply_rules (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  configuration_id uuid NOT NULL,
  keyword varchar(120) NOT NULL CHECK (length(btrim(keyword)) > 0),
  match_mode varchar(20) NOT NULL DEFAULT 'exact' CHECK (match_mode IN ('exact','contains')),
  response_text varchar(4096) NOT NULL CHECK (length(btrim(response_text)) > 0),
  priority integer NOT NULL DEFAULT 100 CHECK (priority >= 0),
  enabled boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (configuration_id,priority),
  FOREIGN KEY (tenant_id,configuration_id) REFERENCES telbot.configuration_versions(tenant_id,id) ON DELETE CASCADE
);

-- @@statement 12
CREATE TABLE telbot.faq_entries (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  configuration_id uuid NOT NULL,
  question varchar(500) NOT NULL CHECK (length(btrim(question)) > 0),
  answer varchar(4096) NOT NULL CHECK (length(btrim(answer)) > 0),
  sort_order integer NOT NULL DEFAULT 0 CHECK (sort_order >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (configuration_id,sort_order),
  FOREIGN KEY (tenant_id,configuration_id) REFERENCES telbot.configuration_versions(tenant_id,id) ON DELETE CASCADE
);

-- @@statement 13
CREATE TABLE telbot.chat_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  bot_id uuid NOT NULL,
  telegram_chat_id bigint NOT NULL,
  status varchar(20) NOT NULL DEFAULT 'open' CHECK (status IN ('open','paused','closed')),
  started_at timestamptz NOT NULL DEFAULT now(),
  last_activity_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (bot_id,telegram_chat_id),
  UNIQUE (tenant_id,bot_id,id),
  FOREIGN KEY (tenant_id,bot_id) REFERENCES telbot.bots(tenant_id,id) ON DELETE RESTRICT
);

-- @@statement 14
CREATE TABLE telbot.inbound_updates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  bot_id uuid NOT NULL,
  session_id uuid,
  telegram_update_id bigint NOT NULL CHECK (telegram_update_id >= 0),
  incoming_text varchar(4096),
  processing_status varchar(24) NOT NULL DEFAULT 'received' CHECK (processing_status IN ('received','queued','processed','ignored','failed')),
  received_at timestamptz NOT NULL DEFAULT now(),
  processed_at timestamptz,
  UNIQUE (bot_id,telegram_update_id),
  UNIQUE (tenant_id,bot_id,id),
  FOREIGN KEY (tenant_id,bot_id) REFERENCES telbot.bots(tenant_id,id) ON DELETE RESTRICT,
  FOREIGN KEY (tenant_id,bot_id,session_id) REFERENCES telbot.chat_sessions(tenant_id,bot_id,id) ON DELETE RESTRICT
);

-- @@statement 15
CREATE TABLE telbot.outbound_messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  bot_id uuid NOT NULL,
  session_id uuid,
  source_update_id uuid,
  response_text varchar(4096) NOT NULL CHECK (length(btrim(response_text)) > 0),
  telegram_message_id bigint,
  delivery_status varchar(20) NOT NULL DEFAULT 'queued' CHECK (delivery_status IN ('queued','sent','failed','cancelled')),
  attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  error_code varchar(100),
  created_at timestamptz NOT NULL DEFAULT now(),
  sent_at timestamptz,
  FOREIGN KEY (tenant_id,bot_id) REFERENCES telbot.bots(tenant_id,id) ON DELETE RESTRICT,
  FOREIGN KEY (tenant_id,bot_id,session_id) REFERENCES telbot.chat_sessions(tenant_id,bot_id,id) ON DELETE RESTRICT,
  FOREIGN KEY (tenant_id,bot_id,source_update_id) REFERENCES telbot.inbound_updates(tenant_id,bot_id,id) ON DELETE RESTRICT,
  CHECK (delivery_status <> 'sent' OR sent_at IS NOT NULL)
);

-- @@statement 16
CREATE TABLE telbot.audit_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES telbot.tenants(id) ON DELETE RESTRICT,
  bot_id uuid,
  actor_telegram_user_id bigint,
  event_type varchar(100) NOT NULL CHECK (length(btrim(event_type)) > 0),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadata) = 'object'),
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (tenant_id,bot_id) REFERENCES telbot.bots(tenant_id,id) ON DELETE RESTRICT
);

-- @@statement 17
CREATE INDEX bots_by_tenant_status ON telbot.bots(tenant_id,status);

-- @@statement 18
CREATE INDEX requests_by_owner_status ON telbot.managed_bot_requests(tenant_id,owner_telegram_user_id,status);

-- @@statement 19
CREATE INDEX configs_by_bot_state ON telbot.configuration_versions(tenant_id,bot_id,state);

-- @@statement 20
CREATE INDEX inbound_by_bot_received ON telbot.inbound_updates(bot_id,received_at DESC);

-- @@statement 21
CREATE INDEX outbound_queue_by_bot ON telbot.outbound_messages(bot_id,created_at) WHERE delivery_status='queued';

-- @@statement 22
CREATE INDEX audit_by_tenant_created ON telbot.audit_events(tenant_id,created_at DESC);

-- @@statement 23
INSERT INTO telbot.schema_migrations(version,description) VALUES ('0001_telbot_foundation','Tenant-scoped no-code Telegram builder schema with bot ownership, versioned configurations, webhooks, audit');
