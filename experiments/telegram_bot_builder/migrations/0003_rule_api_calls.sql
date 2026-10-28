-- Additive TelBot UAT only. Apply transactionally after 0002, never Production.
DO $$ BEGIN
 IF current_database() <> 'telbot'
    OR NOT EXISTS (SELECT 1 FROM telbot.schema_migrations WHERE version='0002_webhook_auth')
    OR EXISTS (SELECT 1 FROM telbot.schema_migrations WHERE version='0003_rule_api_calls') THEN
   RAISE EXCEPTION 'Invalid TelBot migration state';
 END IF;
END $$;
ALTER TABLE telbot.reply_rules
 ADD COLUMN action_type varchar(10) NOT NULL DEFAULT 'text' CHECK (action_type IN ('text','api')),
 ADD COLUMN api_request_ciphertext bytea,
 ADD CONSTRAINT rule_api_ciphertext_required CHECK (
   (action_type='text' AND api_request_ciphertext IS NULL) OR
   (action_type='api' AND api_request_ciphertext IS NOT NULL));
INSERT INTO telbot.schema_migrations(version,description)
VALUES ('0003_rule_api_calls','Versioned rule actions with encrypted HTTP JSON configuration');
