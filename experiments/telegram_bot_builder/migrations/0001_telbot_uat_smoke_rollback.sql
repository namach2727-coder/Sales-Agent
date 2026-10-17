-- DirectPilot TelBot: rollback-only UAT integrity smoke test for foundation migration.
-- Target exclusively Neon curly-cell-93038441 / br-tiny-poetry-arz49v2o / telbot.
-- Entire test dataset is intentionally rolled back via a caught exception.
DO $telbot_smoke$
DECLARE
  tenant_a uuid;
  tenant_b uuid;
  bot_a uuid;
  config_a uuid;
BEGIN
  BEGIN
    INSERT INTO telbot.tenants(display_name) VALUES ('__TELBOT_UAT_ROLLBACK_A__') RETURNING id INTO tenant_a;
    INSERT INTO telbot.tenants(display_name) VALUES ('__TELBOT_UAT_ROLLBACK_B__') RETURNING id INTO tenant_b;
    INSERT INTO telbot.tenant_users(tenant_id,telegram_user_id,role) VALUES
      (tenant_a,10001,'owner'),(tenant_b,20002,'owner');
    INSERT INTO telbot.bots(tenant_id,telegram_bot_id,display_name,owner_telegram_user_id,status)
      VALUES (tenant_a,12345001,'Test Bot A',10001,'pending') RETURNING id INTO bot_a;
    INSERT INTO telbot.configuration_versions(tenant_id,bot_id,version,state,greeting,fallback_reply,created_by_telegram_user_id,published_at)
      VALUES (tenant_a,bot_a,1,'published','Welcome A','Fallback A',10001,now()) RETURNING id INTO config_a;
    INSERT INTO telbot.reply_rules(tenant_id,configuration_id,keyword,response_text,priority)
      VALUES (tenant_a,config_a,'سلام','درود',1);
    INSERT INTO telbot.inbound_updates(tenant_id,bot_id,telegram_update_id,processing_status)
      VALUES (tenant_a,bot_a,99,'received');

    -- A webhook redelivery with the same (bot,update_id) must be rejected.
    BEGIN
      INSERT INTO telbot.inbound_updates(tenant_id,bot_id,telegram_update_id)
        VALUES (tenant_a,bot_a,99);
      RAISE EXCEPTION 'FAIL: duplicate Telegram webhook update accepted';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;

    -- Two concurrently "published" config versions for one bot are not allowed.
    BEGIN
      INSERT INTO telbot.configuration_versions(tenant_id,bot_id,version,state,greeting,fallback_reply,created_by_telegram_user_id,published_at)
        VALUES (tenant_a,bot_a,2,'published','Second Greeting','Second Fallback',10001,now());
      RAISE EXCEPTION 'FAIL: second published bot configuration accepted';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;

    -- A tenant B row must never reference tenant A's published config.
    BEGIN
      INSERT INTO telbot.reply_rules(tenant_id,configuration_id,keyword,response_text,priority)
        VALUES (tenant_b,config_a,'cross-tenant','should fail',88);
      RAISE EXCEPTION 'FAIL: tenant B was allowed to reference tenant A rules';
    EXCEPTION WHEN foreign_key_violation THEN NULL;
    END;

    -- A tenant B bot cannot claim ownership by a user belonging only to tenant A.
    BEGIN
      INSERT INTO telbot.bots(tenant_id,telegram_bot_id,display_name,owner_telegram_user_id,status)
        VALUES (tenant_b,12345002,'Cross Tenant Bot',10001,'pending');
      RAISE EXCEPTION 'FAIL: cross-tenant Telegram owner reference accepted';
    EXCEPTION WHEN foreign_key_violation THEN NULL;
    END;

    -- Active bots cannot be configured without encrypted credentials.
    BEGIN
      INSERT INTO telbot.bots(tenant_id,telegram_bot_id,display_name,owner_telegram_user_id,status)
        VALUES (tenant_b,12345003,'No Credentials',20002,'active');
      RAISE EXCEPTION 'FAIL: activated child bot without encrypted credential';
    EXCEPTION WHEN check_violation THEN NULL;
    END;

    -- Expected error intentionally rolls back ALL positive test fixtures.
    RAISE EXCEPTION '__TELBOT_TEST_ROLLBACK__';
  EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> '__TELBOT_TEST_ROLLBACK__' THEN
      RAISE;
    END IF;
  END;
END
$telbot_smoke$;
