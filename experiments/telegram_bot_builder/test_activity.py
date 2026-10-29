"""Activity authorization/privacy with synthetic identities; no network or writes."""
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from experiments.telegram_bot_builder.api import app, get_connection
from experiments.telegram_bot_builder.test_api import FakeDB, Cursor, TENANT_A, TENANT_B, BOT_A, BOT_B
from experiments.telegram_bot_builder.test_security import signed_initdata


class ActivityDB(FakeDB):
    def execute(self, query, args=()):
        sql=' '.join(query.split())
        if 'SELECT incoming.received' in sql:
            self.commands.append((sql,tuple(args)))
            assert args == (TENANT_A,BOT_A,TENANT_A,BOT_A)
            return Cursor({'received':5,'sent':2,'failed':1,'pending':1,'checked_at':'2026-10-29T16:00:00Z'})
        if 'LEFT JOIN LATERAL' in sql:
            self.commands.append((sql,tuple(args)))
            assert args == (TENANT_A,BOT_A)
            return Cursor(rows=[{'received_at':'2026-10-29T16:00:00Z','processing_status':'processed','delivery_status':'sent','telegram_acknowledged':True}])
        return super().execute(query,args)


class ActivityTests(unittest.TestCase):
    def setUp(self):
        self.db=ActivityDB();app.dependency_overrides[get_connection]=lambda:self.db
        self.env=patch.dict(os.environ,{'TELBOT_ENV':'uat','TELBOT_MANAGER_TOKEN':'111:TESTTOKEN'});self.env.start()
        self.client=TestClient(app);self.url=f'/api/v1/tenants/{TENANT_A}/bots/{BOT_A}/activity'
    def tearDown(self):
        app.dependency_overrides.clear();self.env.stop();self.client.close()
    def test_owner_and_viewer_read_only_metadata(self):
        for actor in [123456,111222]:
            result=self.client.get(self.url,headers={'X-Telegram-Init-Data':signed_initdata(user_id=actor)})
            self.assertEqual(result.status_code,200,result.text)
            data=result.json();self.assertEqual(data['summary']['received'],5)
            self.assertEqual(set(data['events'][0]),{'received_at','processing_status','delivery_status','telegram_acknowledged'})
        self.assertEqual(self.db.commits,0)
        self.assertFalse(any(any(word in sql for word in ['INSERT','UPDATE','DELETE','credential_ciphertext','incoming_text','response_text']) for sql,args in self.db.commands))
    def test_unauthenticated_other_tenant_and_wrong_bot_are_rejected(self):
        self.assertEqual(self.client.get(self.url).status_code,401)
        headers={'X-Telegram-Init-Data':signed_initdata()}
        self.assertEqual(self.client.get(f'/api/v1/tenants/{TENANT_B}/bots/{BOT_A}/activity',headers=headers).status_code,403)
        self.assertEqual(self.client.get(f'/api/v1/tenants/{TENANT_A}/bots/{BOT_B}/activity',headers=headers).status_code,404)
        self.assertFalse(any('SELECT incoming.received' in sql for sql,args in self.db.commands))
        self.assertEqual(self.client.post(self.url,headers=headers,json={}).status_code,405)
