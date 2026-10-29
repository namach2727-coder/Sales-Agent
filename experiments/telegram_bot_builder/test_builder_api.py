import os
import unittest
from uuid import UUID, uuid4
from unittest.mock import patch

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from experiments.telegram_bot_builder.api import app, get_connection
from experiments.telegram_bot_builder.api_actions import ApiCallInput, materialize_call, seal_call, open_call
from experiments.telegram_bot_builder.test_api import FakeDB, Cursor, TENANT_A, TENANT_B, BOT_A
from experiments.telegram_bot_builder.test_security import signed_initdata


class BuilderDB(FakeDB):
    def __init__(self):
        super().__init__(); self.current = {'id':uuid4(), 'version':2, 'greeting':'Hello', 'fallback_reply':'Fallback', 'published_at':None}
        self.rules = []; self.new_id = uuid4(); self.schema_ready=True; self.source=None; self.draft={'id':self.new_id,'version':3,'state':'draft'}
    def execute(self, query, args=()):
        sql = ' '.join(query.split()); self.commands.append((sql,tuple(args)))
        if 'SELECT version FROM telbot.schema_migrations WHERE' in sql:
            return Cursor({'version':'0003_rule_api_calls'} if self.schema_ready else None)
        if 'FROM telbot.configuration_versions' in sql and "state='published'" in sql: return Cursor(self.current)
        if 'FROM telbot.configuration_versions' in sql and 'FOR UPDATE' in sql: return Cursor(self.draft)
        if 'SELECT COALESCE(MAX(version)' in sql: return Cursor({'n':3})
        if 'SELECT id FROM telbot.bots' in sql: return Cursor({'id':BOT_A}) if args==(TENANT_A,BOT_A) else Cursor(None)
        if 'SELECT r.api_request_ciphertext' in sql: return Cursor(self.source)
        if 'SELECT id,keyword,match_mode' in sql: return Cursor(rows=self.rules)
        if 'INSERT INTO telbot.configuration_versions' in sql: return Cursor(self.draft)
        if sql.startswith(('INSERT INTO telbot.reply_rules','INSERT INTO telbot.menu_buttons','INSERT INTO telbot.faq_entries','UPDATE telbot.configuration_versions')): return Cursor(None)
        return super().execute(query,args)


class BuilderApiTests(unittest.TestCase):
    def setUp(self):
        self.db=BuilderDB(); self.key=Fernet.generate_key().decode()
        app.dependency_overrides[get_connection]=lambda:self.db
        self.env=patch.dict(os.environ,{'TELBOT_MANAGER_TOKEN':'111:TESTTOKEN','TELBOT_ENV':'uat','TELBOT_TOKEN_FERNET_KEY':self.key});self.env.start()
        self.client=TestClient(app);self.headers={'X-Telegram-Init-Data':signed_initdata()}
        self.base=f'/api/v1/tenants/{TENANT_A}/bots/{BOT_A}'
    def tearDown(self):
        app.dependency_overrides.clear();self.env.stop();self.client.close()
    def post(self, rules, **extra):
        return self.client.post(self.base+'/configs',headers=self.headers,json={'greeting':'Hello','fallback_reply':'Fallback','rules':rules,'base_version':2,**extra})

    def test_several_rules_saved_in_one_version_with_explicit_order(self):
        result=self.post([{'keyword':'قیمت','response_text':'Price'}, {'keyword':'آدرس','match_mode':'contains','response_text':'Address','enabled':False}])
        self.assertEqual(result.status_code,201,result.text)
        inserts=[a for q,a in self.db.commands if q.startswith('INSERT INTO telbot.reply_rules')]
        self.assertEqual([a[5] for a in inserts],[0,1]);self.assertEqual([a[6] for a in inserts],[True,False])
        self.assertTrue(all(a[:2]==(TENANT_A,self.db.new_id) for a in inserts))
        self.assertTrue(any('INSERT INTO telbot.menu_buttons' in q for q,a in self.db.commands))
        self.assertTrue(any('INSERT INTO telbot.faq_entries' in q for q,a in self.db.commands))
        self.assertEqual(self.db.commits,1)

    def test_legacy_client_omitting_rules_preserves_rules(self):
        response=self.client.post(self.base+'/configs',headers=self.headers,json={'greeting':'Hi','fallback_reply':'Other'})
        self.assertEqual(response.status_code,201,response.text)
        self.assertTrue(any('SELECT tenant_id,%s,keyword' in q for q,a in self.db.commands))

    def test_api_secret_encrypted_and_never_returned(self):
        call={'url':'https://api.example.com/a','auth_mode':'bearer','credential':'synthetic-private-key','response_path':'answer'}
        result=self.post([{'keyword':'api','response_text':'Unavailable','action_type':'api','api':call}])
        self.assertEqual(result.status_code,201,result.text);self.assertNotIn('synthetic-private-key',result.text)
        inserted=next(a for q,a in self.db.commands if q.startswith('INSERT INTO telbot.reply_rules'))
        self.assertEqual(inserted[7],'api');self.assertIsInstance(inserted[8],bytes);self.assertNotIn(b'synthetic-private-key',inserted[8])
        self.db.rules=[{'id':uuid4(),'keyword':'api','match_mode':'exact','response_text':'Unavailable','priority':0,'enabled':True,'action_type':'api','api_request_ciphertext':inserted[8]}]
        public=self.client.get(self.base+'/config',headers=self.headers)
        self.assertEqual(public.status_code,200,public.text);self.assertNotIn('synthetic-private-key',public.text);self.assertNotIn('ciphertext',public.text)
        self.assertTrue(public.json()['rules'][0]['api']['credential_present'])

    def test_cross_scope_secret_reference_cannot_be_reused(self):
        response=self.post([{'keyword':'api','response_text':'Unavailable','action_type':'api','source_rule_id':str(uuid4()),'api':{'url':'https://api.example.com/a','auth_mode':'bearer'}}])
        self.assertEqual(response.status_code,409,response.text);self.assertEqual(self.db.commits,0)
        query,args=next((q,a) for q,a in self.db.commands if 'SELECT r.api_request_ciphertext' in q)
        self.assertEqual(args[1:],(TENANT_A,BOT_A,self.db.current['id']))

    def test_same_scope_secret_can_be_retained_without_readback(self):
        value=materialize_call(ApiCallInput(url='https://api.example.com/a',auth_mode='bearer',credential='synthetic'))
        self.db.source={'api_request_ciphertext':seal_call(value,self.key)}
        response=self.post([{'keyword':'api','response_text':'Unavailable','action_type':'api','source_rule_id':str(uuid4()),'api':{'url':'https://api.example.com/a','auth_mode':'bearer'}}])
        self.assertEqual(response.status_code,201,response.text)
        new=next(a[8] for q,a in self.db.commands if q.startswith('INSERT INTO telbot.reply_rules'))
        self.assertEqual(open_call(new,self.key)['credential'],'synthetic')

    def test_no_schema_still_allows_text_but_not_api(self):
        self.db.schema_ready=False
        self.assertEqual(self.post([{'keyword':'hello','response_text':'Hi'}]).status_code,201)
        response=self.post([{'keyword':'api','response_text':'No','action_type':'api','api':{'url':'https://api.example.com/a'}}])
        self.assertEqual(response.status_code,503)

    def test_stale_save_and_publish_are_rejected(self):
        self.assertEqual(self.post([],base_version=1).status_code,409)
        response=self.client.post(self.base+f'/configs/{self.db.new_id}/publish?expected_version=1',headers=self.headers)
        self.assertEqual(response.status_code,409,response.text);self.assertEqual(self.db.commits,0)

    def test_viewer_and_other_tenant_cannot_write(self):
        for headers,url in [({'X-Telegram-Init-Data':signed_initdata(user_id=111222)},self.base),
                            (self.headers,f'/api/v1/tenants/{TENANT_B}/bots/{BOT_A}')]:
            response=self.client.post(url+'/configs',headers=headers,json={'greeting':'Hi','fallback_reply':'Other','rules':[]})
            self.assertEqual(response.status_code,403,response.text)

    def test_validation_does_not_echo_sensitive_body(self):
        for data in [dict(credential='synthetic-secret\ninvalid'),dict(credential='synthetic-secret',url='http://bad.example.com')]:
            call={'url':'https://api.example.com/a','auth_mode':'bearer',**data}
            response=self.post([{'keyword':'api','response_text':'No','action_type':'api','api':call}])
            self.assertEqual(response.status_code,422,response.text);self.assertNotIn('synthetic-secret',response.text)
        self.assertEqual(self.post([{'keyword':'a','response_text':'b'}]*101).status_code,422)
        self.assertEqual(self.post([{'keyword':'  ','response_text':'b'}]).status_code,422)


    def test_button_limits_and_backward_compatible_menu_preservation(self):
        self.assertEqual(self.post([{'keyword':'x'*65,'response_text':'Answer','show_button':True}]).status_code,422)
        self.assertEqual(self.post([{'keyword':str(i),'response_text':'Answer','show_button':True} for i in range(13)]).status_code,422)
        result=self.post([{'keyword':'قیمت','response_text':'Price','show_button':True},{'keyword':'آدرس','response_text':'Address','show_button':False}])
        self.assertEqual(result.status_code,201,result.text)
        buttons=[args for sql,args in self.db.commands if "VALUES (%s,%s,%s,'reply'" in sql]
        self.assertEqual(buttons,[(TENANT_A,self.db.new_id,'قیمت','قیمت',0)])


    def test_explicit_empty_reply_snapshot_clears_owned_buttons_without_dropping_legacy(self):
        result=self.post([],replace_reply_buttons=True)
        self.assertEqual(result.status_code,201,result.text)
        copies=[sql for sql,args in self.db.commands if 'INSERT INTO telbot.menu_buttons' in sql]
        self.assertTrue(any('AND NOT' in sql and 'EXISTS' in sql for sql in copies))
