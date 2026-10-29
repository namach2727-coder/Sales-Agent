"""Tenant-guarded pause/resume without provider calls or customer data."""
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from experiments.telegram_bot_builder.api import app, get_connection
from experiments.telegram_bot_builder.test_api import FakeDB, Cursor, TENANT_A, TENANT_B, BOT_A, BOT_B
from experiments.telegram_bot_builder.test_security import signed_initdata


class StateDB(FakeDB):
    def __init__(self):super().__init__();self.state='active';self.ready=True;self.race=False
    def execute(self,query,args=()):
        sql=' '.join(query.split())
        if 'SELECT tu.role' in sql and args==(TENANT_A,333444):return Cursor({'role':'editor'})
        if sql.startswith('SELECT id,telegram_bot_id'):
            self.commands.append((sql,tuple(args)))
            return Cursor({'id':BOT_A,'status':self.state}) if args==(TENANT_A,BOT_A) and self.state!='revoked' else Cursor(None)
        if sql.startswith('UPDATE telbot.bots SET status='):
            self.commands.append((sql,tuple(args)))
            desired,tenant,bot,expected=args
            if not self.ready or self.race or self.state!=expected:return Cursor(None)
            assert (tenant,bot)==(TENANT_A,BOT_A)
            self.state=desired;return Cursor({'status':desired})
        if sql.startswith('INSERT INTO telbot.audit_events'):
            self.commands.append((sql,tuple(args)));return Cursor(None)
        return super().execute(query,args)


class ReplyStateTests(unittest.TestCase):
    def setUp(self):
        self.db=StateDB();app.dependency_overrides[get_connection]=lambda:self.db
        self.env=patch.dict(os.environ,{'TELBOT_ENV':'uat','TELBOT_MANAGER_TOKEN':'111:TESTTOKEN','TELBOT_REPLIES_ENABLED':'true'});self.env.start()
        self.client=TestClient(app);self.url=f'/api/v1/tenants/{TENANT_A}/bots/{BOT_A}/reply-state'
        self.headers={'X-Telegram-Init-Data':signed_initdata()}
    def tearDown(self):app.dependency_overrides.clear();self.env.stop();self.client.close()
    def test_owner_pause_editor_resume_audited_without_settings_or_network(self):
        result=self.client.post(self.url,headers=self.headers,json={'paused':True,'expected_status':'active'})
        self.assertEqual(result.status_code,200,result.text);self.assertEqual(result.json()['status'],'paused')
        result=self.client.post(self.url,headers={'X-Telegram-Init-Data':signed_initdata(user_id=333444)},json={'paused':False,'expected_status':'paused'})
        self.assertEqual(result.status_code,200,result.text);self.assertEqual(result.json(),{'status':'active','runtime_enabled':True})
        events=[args[-1] for sql,args in self.db.commands if sql.startswith('INSERT INTO telbot.audit_events')]
        self.assertEqual(events,['bot_replies_paused','bot_replies_resumed']);self.assertEqual(self.db.commits,2)
        self.assertFalse(any('configuration_versions' in sql for sql,args in self.db.commands))
    def test_auth_viewer_tenant_and_bot_guards(self):
        body={'paused':True,'expected_status':'active'}
        self.assertEqual(self.client.post(self.url,json=body).status_code,401)
        self.assertEqual(self.client.post(self.url,headers={'X-Telegram-Init-Data':signed_initdata(user_id=111222)},json=body).status_code,403)
        self.assertEqual(self.client.post(f'/api/v1/tenants/{TENANT_B}/bots/{BOT_A}/reply-state',headers=self.headers,json=body).status_code,403)
        self.assertEqual(self.client.post(f'/api/v1/tenants/{TENANT_A}/bots/{BOT_B}/reply-state',headers=self.headers,json=body).status_code,404)
        self.assertEqual(self.db.commits,0)
    def test_stale_pending_revoked_or_missing_activation_cannot_resume(self):
        for mode in ['stale','pending','revoked','unready','race']:
            self.db.state='paused';self.db.ready=True;self.db.race=False
            if mode in ['pending','revoked']:self.db.state=mode
            if mode=='unready':self.db.ready=False
            if mode=='race':self.db.race=True
            expected='active' if mode=='stale' else 'paused'
            result=self.client.post(self.url,headers=self.headers,json={'paused':False,'expected_status':expected})
            self.assertEqual(result.status_code,404 if mode=='revoked' else 409,result.text)
        self.assertEqual(self.db.commits,0)
    def test_noop_does_not_duplicate_audit_and_global_off_stays_off(self):
        with patch.dict(os.environ,{'TELBOT_REPLIES_ENABLED':'false'}):
            result=self.client.post(self.url,headers=self.headers,json={'paused':False,'expected_status':'active'})
        self.assertEqual(result.status_code,200,result.text);self.assertFalse(result.json()['runtime_enabled'])
        self.assertEqual(self.db.commits,0)
        self.assertEqual(self.client.post(self.url,headers=self.headers,json={'paused':True,'expected_status':'pending'}).status_code,422)
