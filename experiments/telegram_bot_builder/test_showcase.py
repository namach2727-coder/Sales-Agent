import os
import unittest
from unittest.mock import patch
from uuid import uuid4
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from experiments.telegram_bot_builder.showcase import *
from experiments.telegram_bot_builder.showcase_runtime import seal,unseal,ShowcaseError,process_showcase
from experiments.telegram_bot_builder.api import app,get_connection
from experiments.telegram_bot_builder.test_api import FakeDB,TENANT_A,BOT_A
from experiments.telegram_bot_builder.test_security import signed_initdata

class ShowcaseConversationTests(unittest.TestCase):
    def test_catalog_has_distinct_options_and_all_paths_remain_simulated(self):
        self.assertEqual(len(CATALOG),24);self.assertEqual(len(BY_ID),24)
        for x in CATALOG:
            r=transition({},'/start idea_'+x.id);self.assertEqual(r.state['industry'],x.id)
            demo=transition(r.state,TRY);self.assertIn('نمایش',demo.text)
            result=transition(demo.state,x.choices[0]);self.assertIn('نمونه',result.text);self.assertIsNone(result.inquiry)
            self.assertEqual(transition(result.state,CHOOSE).state['step'],'description')
        for n in range(4):
            r=page(n);self.assertEqual(r.state['page'],n);self.assertTrue(all(len(row)<=2 for row in r.rows))

    def test_consent_review_edit_cancel_and_one_submission(self):
        r=transition({},'/start idea_shop');r=transition(r.state,CHOOSE)
        r=transition(r.state,'برای فروشگاه خودم ربات سفارش می‌خواهم')
        self.assertEqual(r.state['step'],'contact');self.assertIsNone(r.inquiry)
        r=transition(r.state,SKIP,'sample_user');self.assertEqual(r.state['contact'],'@sample_user')
        self.assertIn('شناسهٔ تلگرام',r.text);self.assertIsNone(r.inquiry)
        done=transition(r.state,CONFIRM);self.assertEqual(done.inquiry['industry'],'shop')
        self.assertIsNone(transition(done.state,CONFIRM).inquiry)
        self.assertEqual(transition(r.state,EDIT).state['step'],'description')
        self.assertFalse(transition(r.state,CANCEL).state)

    def test_free_text_limits_reset_and_unknown_category(self):
        state=ask_description('other').state
        for bad in ('a','x'*1201):self.assertEqual(transition(state,bad).state,state)
        r=transition(state,'پشتیبانی مشتری فروشگاه ما');r=transition(r.state,SKIP,'<bad>')
        self.assertNotIn('<bad>',r.text)
        self.assertFalse(transition(r.state,HOME).state)
        self.assertIsNone(transition({},'✅ تأیید و ارسال درخواست').inquiry)

    def test_sensitive_state_encrypted_and_errors_categorical(self):
        key=Fernet.generate_key().decode()
        with patch.dict(os.environ,{'TELBOT_TOKEN_FERNET_KEY':key}):
            s=seal({'description':'synthetic private need'});self.assertNotIn(b'synthetic private',s)
            self.assertEqual(unseal(s)['description'],'synthetic private need')
            with self.assertRaisesRegex(ShowcaseError,'^showcase_storage_unavailable$'):unseal(b'bad')

class ShowcaseAPITests(unittest.TestCase):
    def tearDown(self):app.dependency_overrides.clear()
    def test_public_page_assets_safe_catalog_and_no_request_submission_endpoint(self):
        app.dependency_overrides[get_connection]=lambda:FakeDB()
        with patch.dict(os.environ,{'TELBOT_ENV':'uat','TELBOT_SHOWCASE_ENABLED':'false'}),TestClient(app) as c:
            self.assertEqual(c.get('/showcase').status_code,200)
            self.assertEqual(c.get('/showcase/showcase.js').status_code,200)
            self.assertEqual(c.get('/showcase/private.env').status_code,404)
            data=c.get('/api/v1/showcase/catalog').json();self.assertEqual(len(data['industries']),24);self.assertIsNone(data['bot_url'])
            self.assertEqual(c.post('/api/v1/showcase/catalog',json={'description':'unauthorized'}).status_code,405)
    def test_inbox_auth_scope_and_non_owner_denial(self):
        app.dependency_overrides[get_connection]=lambda:FakeDB()
        with patch.dict(os.environ,{'TELBOT_ENV':'uat','TELBOT_MANAGER_TOKEN':'111:TESTTOKEN','TELBOT_SHOWCASE_ENABLED':'false'}),TestClient(app) as c:
            url=f'/api/v1/tenants/{TENANT_A}/bots/{BOT_A}/showcase-inquiries'
            self.assertEqual(c.get(url).status_code,401)
            # Unknown bot/tenant must never expose inquiry records.
            self.assertEqual(c.get(f'/api/v1/tenants/{uuid4()}/bots/{uuid4()}/showcase-inquiries',headers={'X-Telegram-Init-Data':signed_initdata()}).status_code,403)
