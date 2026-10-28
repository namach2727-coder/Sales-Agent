-- Run only in an isolated empty test branch; outer savepoint is rolled back.
DO $$
DECLARE
 tenant_a uuid := gen_random_uuid(); tenant_b uuid := gen_random_uuid();
 bot_a uuid := gen_random_uuid(); config_a uuid := gen_random_uuid(); config_b uuid := gen_random_uuid();
 BEGIN
 INSERT INTO telbot.tenants(id,display_name) VALUES (tenant_a,'Synthetic A'),(tenant_b,'Synthetic B');
 INSERT INTO telbot.tenant_users(tenant_id,telegram_user_id) VALUES (tenant_a,1001),(tenant_b,1002);
 INSERT INTO telbot.bots(id,tenant_id,telegram_bot_id,display_name,owner_telegram_user_id)
 VALUES (bot_a,tenant_a,12345678,'Synthetic test',1001);
 INSERT INTO telbot.configuration_versions(id,tenant_id,bot_id,version,greeting,fallback_reply,created_by_telegram_user_id,state,published_at)
 VALUES (config_a,tenant_a,bot_a,1,'Hi','Fallback',1001,'published',now());
 INSERT INTO telbot.reply_rules(tenant_id,configuration_id,keyword,response_text,priority)
 VALUES (tenant_a,config_a,'price','Price',0),(tenant_a,config_a,'address','Address',1);
 IF (SELECT count(*) FROM telbot.reply_rules WHERE configuration_id=config_a AND action_type='text') <> 2 THEN
 RAISE EXCEPTION 'Legacy text default failed'; END IF;
 INSERT INTO telbot.reply_rules(tenant_id,configuration_id,keyword,response_text,priority,action_type,api_request_ciphertext)
 VALUES (tenant_a,config_a,'stock','Unavailable',2,'api',convert_to('synthetic-ciphertext','UTF8'));
 BEGIN
 INSERT INTO telbot.reply_rules(tenant_id,configuration_id,keyword,response_text,priority,action_type)
 VALUES (tenant_a,config_a,'bad','Unavailable',3,'api');
 RAISE EXCEPTION 'API plaintext protection failed';
 EXCEPTION WHEN check_violation THEN NULL; END;
 BEGIN
 INSERT INTO telbot.reply_rules(tenant_id,configuration_id,keyword,response_text,priority,action_type,api_request_ciphertext)
 VALUES (tenant_a,config_a,'bad','No',3,'text',convert_to('synthetic','UTF8'));
 RAISE EXCEPTION 'Text ciphertext constraint failed';
 EXCEPTION WHEN check_violation THEN NULL; END;
 BEGIN
 INSERT INTO telbot.reply_rules(tenant_id,configuration_id,keyword,response_text,priority)
 VALUES (tenant_b,config_a,'bad','Cross tenant',3);
 RAISE EXCEPTION 'Cross tenant reference accepted';
 EXCEPTION WHEN foreign_key_violation THEN NULL; END;
 BEGIN
 INSERT INTO telbot.reply_rules(tenant_id,configuration_id,keyword,response_text,priority)
 VALUES (tenant_a,config_a,'bad','Duplicate priority',0);
 RAISE EXCEPTION 'Duplicate priority accepted';
 EXCEPTION WHEN unique_violation THEN NULL; END;
 INSERT INTO telbot.configuration_versions(id,tenant_id,bot_id,version,greeting,fallback_reply,created_by_telegram_user_id)
 VALUES (config_b,tenant_a,bot_a,2,'New hello','New fallback',1001);
 INSERT INTO telbot.reply_rules(tenant_id,configuration_id,keyword,match_mode,response_text,priority,enabled,action_type,api_request_ciphertext)
 SELECT tenant_id,config_b,keyword,match_mode,response_text,priority,enabled,action_type,api_request_ciphertext
 FROM telbot.reply_rules WHERE configuration_id=config_a AND tenant_id=tenant_a;
 UPDATE telbot.configuration_versions SET state='archived' WHERE id=config_a;
 UPDATE telbot.configuration_versions SET state='published',published_at=now() WHERE id=config_b;
 IF (SELECT count(*) FROM telbot.reply_rules WHERE configuration_id=config_a) <> 3
    OR (SELECT count(*) FROM telbot.reply_rules WHERE configuration_id=config_b) <> 3 THEN
 RAISE EXCEPTION 'Version history preservation failed'; END IF;
 END $$;
