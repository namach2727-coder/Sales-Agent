"""Real migration/snapshot tests; only a disposable loopback CI database is allowed."""
import os
from pathlib import Path
import unittest
import socket
import subprocess
import threading
import time
from uuid import uuid4
from urllib.parse import urlsplit
from unittest.mock import patch

import psycopg
from psycopg.rows import dict_row
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from experiments.telegram_bot_builder.api import app, get_connection
from experiments.telegram_bot_builder.test_security import signed_initdata


@unittest.skipUnless(os.getenv('TELBOT_TEST_DATABASE_URL'), 'Disposable PostgreSQL test service not configured')
class BuilderPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url=os.environ['TELBOT_TEST_DATABASE_URL'];uri=urlsplit(url)
        if uri.hostname not in ('127.0.0.1','localhost') or uri.path!='/telbot' or uri.username!='telbot_test':
            raise RuntimeError('Only disposable loopback test database is allowed')
        cls.url=url;db=psycopg.connect(url,row_factory=dict_row)
        root=Path(__file__).parent/'migrations'
        for name in ['0001_telbot_foundation.sql','0002_webhook_auth.sql']:db.execute((root/name).read_text())
        cls.legacy_tenant=uuid4();cls.legacy_bot=uuid4();cls.legacy_config=uuid4()
        db.execute("INSERT INTO telbot.tenants(id,display_name) VALUES (%s,'Synthetic legacy')",(cls.legacy_tenant,))
        db.execute("INSERT INTO telbot.tenant_users(tenant_id,telegram_user_id) VALUES (%s,123456)",(cls.legacy_tenant,))
        db.execute("INSERT INTO telbot.bots(id,tenant_id,telegram_bot_id,display_name,owner_telegram_user_id) VALUES (%s,%s,12340000,'Legacy',123456)",(cls.legacy_bot,cls.legacy_tenant))
        db.execute("INSERT INTO telbot.configuration_versions(id,tenant_id,bot_id,version,greeting,fallback_reply,created_by_telegram_user_id) VALUES (%s,%s,%s,1,'Hi','Other',123456)",(cls.legacy_config,cls.legacy_tenant,cls.legacy_bot))
        db.execute("INSERT INTO telbot.reply_rules(tenant_id,configuration_id,keyword,response_text) VALUES (%s,%s,'price','Legacy price')",(cls.legacy_tenant,cls.legacy_config))
        db.execute((root/'0003_rule_api_calls.sql').read_text());db.execute((root/'0004_showcase_inquiries.sql').read_text());db.commit();db.close()

    def test_upgrade_preserves_legacy_rule(self):
        with psycopg.connect(self.url,row_factory=dict_row) as db:
            rule=db.execute('SELECT response_text,action_type,api_request_ciphertext FROM telbot.reply_rules WHERE configuration_id=%s',(self.legacy_config,)).fetchone()
            self.assertEqual(rule,{'response_text':'Legacy price','action_type':'text','api_request_ciphertext':None})
            with db.transaction():
                db.execute('SAVEPOINT constraints')
                db.execute((Path(__file__).parent/'migrations'/'0003_rule_api_calls_smoke.sql').read_text())
                db.execute('ROLLBACK TO SAVEPOINT constraints')

    @unittest.skipUnless(os.getenv('TELBOT_TEST_UI_ROUNDTRIP') == 'true', 'Disposable UI/HTTP roundtrip not enabled')
    def test_ui_add_save_close_reopen_against_real_api_and_database(self):
        import uvicorn
        tenant, bot, actor = uuid4(), uuid4(), 333555
        with psycopg.connect(self.url, row_factory=dict_row) as db:
            db.execute("INSERT INTO telbot.tenants(id,display_name) VALUES (%s,'Synthetic UI workspace')", (tenant,))
            db.execute('INSERT INTO telbot.tenant_users(tenant_id,telegram_user_id) VALUES (%s,%s)', (tenant,actor))
            db.execute("INSERT INTO telbot.bots(id,tenant_id,telegram_bot_id,display_name,owner_telegram_user_id) VALUES (%s,%s,12340002,'Synthetic UI bot',%s)", (bot,tenant,actor))
            db.execute("INSERT INTO telbot.configuration_versions(tenant_id,bot_id,version,state,greeting,fallback_reply,created_by_telegram_user_id,published_at) VALUES (%s,%s,1,'published','Hello','Fallback',%s,now())", (tenant,bot,actor))

        def connection():
            with psycopg.connect(self.url, row_factory=dict_row) as db:
                yield db

        app.dependency_overrides[get_connection] = connection
        sock = socket.socket(); sock.bind(('127.0.0.1', 0)); sock.listen(128)
        server = uvicorn.Server(uvicorn.Config(app, log_level='error', lifespan='off', proxy_headers=False))
        thread = threading.Thread(target=server.run, kwargs={'sockets':[sock]}, daemon=True)
        try:
            with patch.dict(os.environ, {'TELBOT_MANAGER_TOKEN':'111:TESTTOKEN', 'TELBOT_ENV':'uat'}):
                thread.start()
                for _ in range(300):
                    if server.started:
                        break
                    time.sleep(.01)
                self.assertTrue(server.started, 'Loopback API did not start')
                result = subprocess.run(
                    ['node', str(Path(__file__).with_name('test_builder_ui_roundtrip.cjs'))],
                    env={**os.environ, 'TELBOT_UI_TEST_ORIGIN':f'http://127.0.0.1:{sock.getsockname()[1]}',
                         'TELBOT_UI_TEST_INIT_DATA':signed_initdata(user_id=actor)},
                    capture_output=True, text=True, timeout=45,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('save/reopen: PASS', result.stdout)
                print(result.stdout.strip())
            with psycopg.connect(self.url, row_factory=dict_row) as db:
                current = db.execute("SELECT id,version FROM telbot.configuration_versions WHERE tenant_id=%s AND bot_id=%s AND state='published'", (tenant,bot)).fetchone()
                self.assertEqual(current['version'], 3)
                self.assertEqual(db.execute('SELECT count(*) AS n FROM telbot.reply_rules WHERE configuration_id=%s', (current['id'],)).fetchone()['n'], 2)
                self.assertEqual(db.execute('SELECT count(*) AS n FROM telbot.configuration_versions WHERE bot_id=%s', (bot,)).fetchone()['n'], 3)
        finally:
            server.should_exit = True
            if thread.ident is not None:
                thread.join(timeout=5)
            sock.close()
            app.dependency_overrides.clear()

    def test_real_snapshot_publish_and_credential_preservation(self):
        tenant,bot=uuid4(),uuid4();key=Fernet.generate_key().decode()
        with psycopg.connect(self.url,row_factory=dict_row) as db:
            db.execute("INSERT INTO telbot.tenants(id,display_name) VALUES (%s,'Synthetic tenant')",(tenant,))
            db.execute('INSERT INTO telbot.tenant_users(tenant_id,telegram_user_id) VALUES (%s,123456)',(tenant,))
            db.execute("INSERT INTO telbot.bots(id,tenant_id,telegram_bot_id,display_name,owner_telegram_user_id) VALUES (%s,%s,12340001,'Synthetic bot',123456)",(bot,tenant));db.commit()
        def connection():
            with psycopg.connect(self.url,row_factory=dict_row) as db:yield db
        app.dependency_overrides[get_connection]=connection
        try:
            with patch.dict(os.environ,{'TELBOT_MANAGER_TOKEN':'111:TESTTOKEN','TELBOT_ENV':'uat','TELBOT_TOKEN_FERNET_KEY':key}),TestClient(app) as client:
                headers={'X-Telegram-Init-Data':signed_initdata()};base=f'/api/v1/tenants/{tenant}/bots/{bot}'
                body={'greeting':'Hello','fallback_reply':'Fallback','base_version':0,'rules':[
                    {'keyword':'price','response_text':'Price','show_button':True},
                    {'keyword':'stock','response_text':'Unavailable','action_type':'api','api':{'url':'https://api.example.com/stock','auth_mode':'bearer','credential':'synthetic-not-real','response_path':'text'}}]}
                first=client.post(base+'/configs',headers=headers,json=body);self.assertEqual(first.status_code,201,first.text)
                first_id=first.json()['id']
                result=client.post(base+f'/configs/{first_id}/publish?expected_version=0',headers=headers);self.assertEqual(result.status_code,200,result.text)
                current=client.get(base+'/config',headers=headers);self.assertEqual(current.status_code,200,current.text)
                self.assertNotIn('synthetic-not-real',current.text);data=current.json();self.assertEqual(len(data['rules']),2)
                self.assertTrue(data['rules'][0]['show_button'])
                with psycopg.connect(self.url,row_factory=dict_row) as db:
                    db.execute("INSERT INTO telbot.menu_buttons(tenant_id,configuration_id,label,action_type,action_value,sort_order) VALUES (%s,%s,'Legacy','reply','Legacy',1)",(tenant,first_id))
                body['rules'][0]['show_button']=False
                body['base_version']=1;body['greeting']='New greeting';body['rules'][1]['source_rule_id']=data['rules'][1]['id'];body['rules'][1]['api']['credential']=None
                from copy import deepcopy
                copied=deepcopy(body['rules'][1]);copied['keyword']='stock copy';body['rules'].append(copied)
                second=client.post(base+'/configs',headers=headers,json=body);self.assertEqual(second.status_code,201,second.text)
                second_id=second.json()['id']
                result=client.post(base+f'/configs/{second_id}/publish?expected_version=1',headers=headers);self.assertEqual(result.status_code,200,result.text)
                stale=client.post(base+'/configs',headers=headers,json=body);self.assertEqual(stale.status_code,409,stale.text)
                with psycopg.connect(self.url,row_factory=dict_row) as db:
                    menus=db.execute('SELECT label FROM telbot.menu_buttons WHERE configuration_id=%s ORDER BY sort_order',(second_id,)).fetchall()
                    self.assertEqual(menus,[{'label':'Legacy'}],'Unrelated legacy menus survive clearing new buttons')
                    archived=db.execute("SELECT count(*) AS n FROM telbot.menu_buttons WHERE configuration_id=%s AND label='price'",(first_id,)).fetchone()
                    self.assertEqual(archived['n'],1,'Archived menu is immutable')
                    self.assertEqual(db.execute('SELECT state FROM telbot.configuration_versions WHERE id=%s',(first_id,)).fetchone()['state'],'archived')
                    self.assertEqual(db.execute('SELECT count(*) AS n FROM telbot.reply_rules WHERE configuration_id=%s',(first_id,)).fetchone()['n'],2)
                    self.assertEqual(db.execute('SELECT count(*) AS n FROM telbot.reply_rules WHERE configuration_id=%s',(second_id,)).fetchone()['n'],3)
                copied_public=client.get(base+'/config',headers=headers)
                self.assertEqual(copied_public.status_code,200,copied_public.text)
                self.assertTrue(copied_public.json()['rules'][2]['api']['credential_present'])
                self.assertNotIn('synthetic-not-real',copied_public.text)
        finally:app.dependency_overrides.clear()


    def test_real_activity_counts_time_window_tenant_isolation_and_privacy(self):
        tenant,other,bot,foreign=uuid4(),uuid4(),uuid4(),uuid4();actor=777888
        with psycopg.connect(self.url,row_factory=dict_row) as db:
            for t,b,number in [(tenant,bot,12340003),(other,foreign,12340004)]:
                db.execute("INSERT INTO telbot.tenants(id,display_name) VALUES (%s,'Synthetic report')",(t,))
                db.execute("INSERT INTO telbot.tenant_users(tenant_id,telegram_user_id) VALUES (%s,%s)",(t,actor))
                db.execute("INSERT INTO telbot.bots(id,tenant_id,telegram_bot_id,display_name,owner_telegram_user_id) VALUES (%s,%s,%s,'Synthetic report bot',%s)",(b,t,number,actor))
            ids=[]
            for i in range(25):
                ids.append(db.execute("INSERT INTO telbot.inbound_updates(tenant_id,bot_id,telegram_update_id,incoming_text) VALUES (%s,%s,%s,'synthetic-private-body') RETURNING id",(tenant,bot,i)).fetchone()['id'])
            for i,state in enumerate(['sent','sent','failed','queued']):
                db.execute("INSERT INTO telbot.outbound_messages(tenant_id,bot_id,source_update_id,response_text,delivery_status,telegram_message_id,sent_at) VALUES (%s,%s,%s,'synthetic-private-answer',%s,%s,CASE WHEN %s THEN now() ELSE NULL END)",(tenant,bot,ids[i],state,42+i if state=='sent' else None,state=='sent'))
            db.execute("INSERT INTO telbot.outbound_messages(tenant_id,bot_id,response_text,delivery_status,telegram_message_id,sent_at) VALUES (%s,%s,'synthetic-other-tenant','sent',99,now())",(other,foreign))
            db.execute("INSERT INTO telbot.inbound_updates(tenant_id,bot_id,telegram_update_id,received_at) VALUES (%s,%s,999,now()-interval '25 hours')",(tenant,bot))
            db.execute("INSERT INTO telbot.outbound_messages(tenant_id,bot_id,response_text,delivery_status,telegram_message_id,sent_at,created_at) VALUES (%s,%s,'synthetic-old','sent',1,now()-interval '25 hours',now()-interval '25 hours')",(tenant,bot))
        def connection():
            with psycopg.connect(self.url,row_factory=dict_row) as db:yield db
        app.dependency_overrides[get_connection]=connection
        try:
            with patch.dict(os.environ,{'TELBOT_MANAGER_TOKEN':'111:TESTTOKEN','TELBOT_ENV':'uat'}),TestClient(app) as client:
                headers={'X-Telegram-Init-Data':signed_initdata(user_id=actor)}
                result=client.get(f'/api/v1/tenants/{tenant}/bots/{bot}/activity',headers=headers)
                self.assertEqual(result.status_code,200,result.text)
                data=result.json();self.assertEqual(len(data['events']),20)
                self.assertEqual({k:data['summary'][k] for k in ['received','sent','failed','pending']},{'received':25,'sent':2,'failed':1,'pending':1})
                self.assertNotIn('synthetic-private',result.text);self.assertNotIn('synthetic-other',result.text)
                self.assertEqual(client.get(f'/api/v1/tenants/{tenant}/bots/{foreign}/activity',headers=headers).status_code,404)
        finally:app.dependency_overrides.clear()


    def test_real_pause_receipts_resume_and_duplicate_never_replay(self):
        import hashlib
        from unittest.mock import AsyncMock
        from experiments.telegram_bot_builder.vault import TokenVault
        tenant,bot=uuid4(),uuid4();actor=888777;key=Fernet.generate_key().decode()
        secret='synthetic-child-secret';number=12340005
        with psycopg.connect(self.url,row_factory=dict_row) as db:
            db.execute("INSERT INTO telbot.tenants(id,display_name) VALUES (%s,'Synthetic pause')",(tenant,))
            db.execute("INSERT INTO telbot.tenant_users(tenant_id,telegram_user_id) VALUES (%s,%s)",(tenant,actor))
            db.execute("INSERT INTO telbot.bots(id,tenant_id,telegram_bot_id,display_name,owner_telegram_user_id,status,credential_ciphertext,credential_key_version,webhook_secret_digest) VALUES (%s,%s,%s,'Synthetic pause bot',%s,'active',%s,1,%s)",(bot,tenant,number,actor,TokenVault(key).encrypt(str(number)+':synthetic'),hashlib.sha256(secret.encode()).digest()))
            db.execute("INSERT INTO telbot.configuration_versions(tenant_id,bot_id,version,state,greeting,fallback_reply,created_by_telegram_user_id,published_at) VALUES (%s,%s,1,'published','Hello','Fallback',%s,now())",(tenant,bot,actor))
        def connection():
            with psycopg.connect(self.url,row_factory=dict_row) as db:yield db
        app.dependency_overrides[get_connection]=connection
        try:
            with patch.dict(os.environ,{'TELBOT_MANAGER_TOKEN':'111:TESTTOKEN','TELBOT_ENV':'uat','TELBOT_REPLIES_ENABLED':'true','TELBOT_TOKEN_FERNET_KEY':key}),TestClient(app) as client,patch('experiments.telegram_bot_builder.reply_runtime.send_text',new_callable=AsyncMock,return_value=(101,None)) as sender,patch('experiments.telegram_bot_builder.reply_runtime.invoke_api',new_callable=AsyncMock) as provider:
                headers={'X-Telegram-Init-Data':signed_initdata(user_id=actor)};base=f'/api/v1/tenants/{tenant}/bots/{bot}'
                with psycopg.connect(self.url,row_factory=dict_row) as decision, psycopg.connect(self.url,row_factory=dict_row) as changer:
                    decision.execute('SELECT status FROM telbot.bots WHERE tenant_id=%s AND id=%s FOR SHARE',(tenant,bot))
                    changer.execute("SET LOCAL lock_timeout='100ms'")
                    with self.assertRaises(psycopg.errors.LockNotAvailable):
                        changer.execute("UPDATE telbot.bots SET status='paused' WHERE tenant_id=%s AND id=%s",(tenant,bot))
                    changer.rollback();decision.rollback()
                paused=client.post(base+'/reply-state',headers=headers,json={'paused':True,'expected_status':'active'})
                self.assertEqual(paused.status_code,200,paused.text)
                payload={'update_id':9002,'message':{'text':'/start','from':{'id':actor,'is_bot':False},'chat':{'id':actor,'type':'private'}}}
                hook=f'/api/v1/webhooks/bots/{number}';webhook_headers={'X-Telegram-Bot-Api-Secret-Token':secret}
                receipt=client.post(hook,headers=webhook_headers,json=payload);self.assertEqual(receipt.status_code,200,receipt.text)
                sender.assert_not_called();provider.assert_not_called()
                with psycopg.connect(self.url,row_factory=dict_row) as db:
                    self.assertEqual(db.execute('SELECT processing_status FROM telbot.inbound_updates WHERE bot_id=%s',(bot,)).fetchone()['processing_status'],'ignored')
                    self.assertEqual(db.execute('SELECT count(*) AS n FROM telbot.outbound_messages WHERE bot_id=%s',(bot,)).fetchone()['n'],0)
                resumed=client.post(base+'/reply-state',headers=headers,json={'paused':False,'expected_status':'paused'})
                self.assertEqual(resumed.status_code,200,resumed.text)
                duplicate=client.post(hook,headers=webhook_headers,json=payload);self.assertTrue(duplicate.json()['duplicate']);sender.assert_not_called()
                payload['update_id']=9003
                sent=client.post(hook,headers=webhook_headers,json=payload);self.assertEqual(sent.status_code,200,sent.text)
                self.assertEqual(sender.call_count,1);provider.assert_not_called()
                with psycopg.connect(self.url,row_factory=dict_row) as db:
                    self.assertEqual(db.execute("SELECT count(*) AS n FROM telbot.audit_events WHERE bot_id=%s AND event_type IN ('bot_replies_paused','bot_replies_resumed')",(bot,)).fetchone()['n'],2)
        finally:app.dependency_overrides.clear()


    def test_showcase_persistent_conversation_private_inbox_and_notification_failure(self):
        from unittest.mock import AsyncMock
        from experiments.telegram_bot_builder.showcase import CHOOSE,SKIP,CONFIRM
        from experiments.telegram_bot_builder.showcase_runtime import unseal
        from experiments.telegram_bot_builder.vault import TokenVault
        tenant,bot,foreign=uuid4(),uuid4(),uuid4();owner,customer,bot_number=765400,765401,12340051
        key=Fernet.generate_key().decode();secret='synthetic-showcase-webhook'
        import hashlib
        with patch.dict(os.environ,{'TELBOT_TOKEN_FERNET_KEY':key}),psycopg.connect(self.url,row_factory=dict_row) as db:
            db.execute("INSERT INTO telbot.tenants(id,display_name) VALUES (%s,'Synthetic portfolio'),(%s,'Synthetic foreign')",(tenant,foreign))
            db.execute("INSERT INTO telbot.tenant_users(tenant_id,telegram_user_id,role) VALUES (%s,%s,'owner'),(%s,%s,'editor')",(tenant,owner,tenant,customer))
            db.execute("INSERT INTO telbot.bots(id,tenant_id,telegram_bot_id,username,display_name,owner_telegram_user_id,credential_ciphertext,credential_key_version,status,webhook_secret_digest) VALUES (%s,%s,%s,'synthetic_showcase_bot','Synthetic showcase',%s,%s,1,'active',%s)",(bot,tenant,bot_number,owner,TokenVault(key).encrypt(str(bot_number)+':synthetic'),hashlib.sha256(secret.encode()).digest()))
            db.execute('INSERT INTO telbot.showcase_settings(tenant_id,bot_id,enabled) VALUES (%s,%s,true)',(tenant,bot))
        def connection():
            with psycopg.connect(self.url,row_factory=dict_row) as db:yield db
        app.dependency_overrides[get_connection]=connection
        texts=['/start idea_shop',CHOOSE,'ربات برای معرفی و دریافت درخواست فروشگاه می‌خواهم',SKIP,CONFIRM]
        try:
            with patch.dict(os.environ,{'TELBOT_ENV':'uat','TELBOT_REPLIES_ENABLED':'true','TELBOT_SHOWCASE_ENABLED':'true','TELBOT_MANAGER_TOKEN':'111:TESTTOKEN','TELBOT_TOKEN_FERNET_KEY':key}),patch('experiments.telegram_bot_builder.showcase_runtime.send_text',new_callable=AsyncMock,return_value=(None,'delivery_unknown')) as sender,TestClient(app) as client:
                for i,text in enumerate(texts):
                    update={'update_id':9000+i,'message':{'text':text,'from':{'id':customer,'is_bot':False,'username':'synthetic_user'},'chat':{'id':customer,'type':'private'}}}
                    response=client.post(f'/api/v1/webhooks/bots/{bot_number}',json=update,headers={'X-Telegram-Bot-Api-Secret-Token':secret});self.assertEqual(response.status_code,200,response.text)
                self.assertEqual(sender.call_count,6)
                owner_payloads=[x.args[1] for x in sender.call_args_list if x.args[1]['chat_id']==owner]
                self.assertEqual(len(owner_payloads),1);self.assertIn('درخواست جدید',owner_payloads[0]['text'])
                # Callback retry and another Confirm cannot produce another inquiry or notification.
                client.post(f'/api/v1/webhooks/bots/{bot_number}',json=update,headers={'X-Telegram-Bot-Api-Secret-Token':secret})
                self.assertEqual(sender.call_count,6)
                update['update_id']=9010;client.post(f'/api/v1/webhooks/bots/{bot_number}',json=update,headers={'X-Telegram-Bot-Api-Secret-Token':secret})
                with psycopg.connect(self.url,row_factory=dict_row) as db:
                    self.assertEqual(db.execute('SELECT count(*) AS n FROM telbot.showcase_inquiries WHERE bot_id=%s',(bot,)).fetchone()['n'],1)
                    row=db.execute('SELECT payload_ciphertext FROM telbot.showcase_inquiries WHERE bot_id=%s',(bot,)).fetchone()
                    self.assertNotIn(texts[2].encode(),bytes(row['payload_ciphertext']))
                    self.assertEqual(unseal(row['payload_ciphertext'])['description'],texts[2])
                    self.assertEqual(db.execute("SELECT status FROM telbot.showcase_deliveries WHERE bot_id=%s AND kind='owner'",(bot,)).fetchone()['status'],'unknown')
                    self.assertEqual(db.execute('SELECT count(*) AS n FROM telbot.configuration_versions WHERE bot_id=%s',(bot,)).fetchone()['n'],0)
                inbox=f'/api/v1/tenants/{tenant}/bots/{bot}/showcase-inquiries'
                h={'X-Telegram-Init-Data':signed_initdata(user_id=owner)}
                result=client.get(inbox,headers=h);self.assertEqual(result.status_code,200,result.text);self.assertEqual(len(result.json()['items']),1);self.assertEqual(result.json()['items'][0]['notification_status'],'unknown')
                self.assertEqual(client.get(inbox,headers={'X-Telegram-Init-Data':signed_initdata(user_id=customer)}).status_code,403)
                self.assertEqual(client.get(f'/api/v1/tenants/{foreign}/bots/{bot}/showcase-inquiries',headers=h).status_code,403)
                public=client.get('/api/v1/showcase/catalog').json();self.assertNotIn(texts[2],str(public));self.assertEqual(public['bot_url'],'https://t.me/synthetic_showcase_bot')
        finally:app.dependency_overrides.clear()
