"""Synthetic transactional-flow invariant tests. No real provider or payment."""
import os
import unittest
from uuid import uuid4
from unittest.mock import patch
from contextlib import ExitStack
from pydantic import ValidationError
from fastapi.testclient import TestClient
from experiments.telegram_bot_builder.service_flow import Plan,ServiceFlow,FlowError,run_demo
from experiments.telegram_bot_builder.api import app,get_connection
from experiments.telegram_bot_builder.test_api import FakeDB,TENANT_A,TENANT_B,BOT_A,BOT_B
from experiments.telegram_bot_builder.test_security import signed_initdata


def engine(**extra):
    return ServiceFlow(TENANT_A,BOT_A,'synthetic-customer',(Plan(id='basic',title='Demo',amount=100,currency='IRT'),),('checkout.example.com',),**extra)


def checkout(flow):
    call=flow.choose_plan('basic')
    flow.accept_external(call.operation_id,{'order_id':flow.order.id,'payment_ref':'demo-ref','checkout_url':'https://checkout.example.com/demo'})
    return call


def payment(flow,**extra):
    call=flow.check_payment()
    payload={'order_id':flow.order.id,'payment_ref':'demo-ref','paid':True,'amount':100,'currency':'IRT',**extra}
    return call,flow.accept_external(call.operation_id,payload)


class ServiceFlowTests(unittest.TestCase):
    def test_only_verified_payment_can_provision_and_deliver(self):
        flow=engine();first=checkout(flow)
        self.assertIsNone(flow.choose_plan('basic'))
        verified,provision=payment(flow)
        self.assertEqual(provision.kind,'provision');self.assertTrue(flow.payment_verified)
        self.assertEqual(provision.order.amount,100)
        self.assertIsNone(flow.accept_external(verified.operation_id,{}),'Duplicate callback cannot issue a second provision')
        self.assertEqual(flow.pending,provision)
        flow.accept_external(provision.operation_id,{'order_id':flow.order.id,'username':'DEMO','password':'SYNTHETIC-PRIVATE','config_text':'SYNTHETIC-CONFIG'})
        self.assertEqual(flow.phase,'delivered')
        self.assertNotIn('SYNTHETIC-PRIVATE',repr(flow));self.assertNotIn('SYNTHETIC-PRIVATE',repr(flow.account))
        self.assertIsNone(flow.accept_external(provision.operation_id,{}));self.assertIsNone(flow.check_payment())
        self.assertEqual(flow.events.count('provision_requested'),1)

    def test_pending_payment_and_duplicate_customer_input_never_provision(self):
        flow=engine();checkout(flow);call=flow.check_payment()
        self.assertIsNone(flow.check_payment())
        flow.accept_external(call.operation_id,{'order_id':flow.order.id,'payment_ref':'demo-ref','paid':False,'amount':100,'currency':'IRT'})
        self.assertEqual(flow.phase,'awaiting_payment');self.assertFalse(flow.payment_verified)
        with self.assertRaisesRegex(FlowError,'payment_required'):flow._issue('provision')
        self.assertTrue(flow.cancel());self.assertIsNone(flow.check_payment())
        self.assertIsNone(flow.account)

    def test_wrong_order_amount_currency_reference_or_untyped_paid_is_rejected(self):
        for bad in [{'order_id':'other'},{'amount':101},{'currency':'IRR'},{'payment_ref':'other'},{'paid':'true'}]:
            flow=engine();checkout(flow)
            with self.subTest(bad=bad),self.assertRaises(FlowError):payment(flow,**bad)
            self.assertEqual(flow.phase,'review_required');self.assertFalse(flow.payment_verified)
            self.assertNotIn('provision_requested',flow.events)

    def test_scope_separates_operations_and_checkout_host_is_allowlisted(self):
        run=uuid4();a=engine(run_id=run)
        b=ServiceFlow(TENANT_B,BOT_B,'synthetic-customer',a.plans,a.checkout_hosts,run_id=run)
        ca=a.choose_plan('basic');cb=b.choose_plan('basic');self.assertNotEqual(ca.idempotency_key,cb.idempotency_key)
        with self.assertRaisesRegex(FlowError,'unexpected_operation'):b.accept_external(ca.operation_id,{})
        for url in ['http://checkout.example.com/a','https://evil.example/a','https://user:pass@checkout.example.com/a','https://checkout.example.com:8443/a']:
            f=engine();c=f.choose_plan('basic')
            with self.assertRaises(FlowError):f.accept_external(c.operation_id,{'order_id':f.order.id,'payment_ref':'demo','checkout_url':url})
            self.assertFalse(f.payment_verified)

    def test_unknown_provision_is_not_blindly_retried_and_secret_errors_are_redacted(self):
        flow=engine();checkout(flow);_,call=payment(flow)
        flow.transport_unknown(call.operation_id);flow.transport_unknown(call.operation_id)
        self.assertEqual(flow.phase,'review_required');self.assertIsNone(flow.check_payment())
        self.assertIsNone(flow.choose_plan('basic'));self.assertEqual(flow.events.count('provision_requested'),1)
        other=engine();checkout(other);_,op=payment(other)
        with self.assertRaises(FlowError) as error:
            other.accept_external(op.operation_id,{'order_id':other.order.id,'username':'demo','password':'SYNTHETIC-PRIVATE','config_text':''})
        self.assertNotIn('SYNTHETIC-PRIVATE',str(error.exception));self.assertIsNone(other.account)

    def test_plan_price_is_strict_and_payment_polling_is_bounded(self):
        for amount in [True,0,-1,'100',1.5]:
            with self.assertRaises(ValidationError):Plan(id='a',title='Demo',amount=amount,currency='IRT')
        flow=engine();checkout(flow)
        for i in range(10):payment(flow,paid=False)
        self.assertIsNone(flow.check_payment());self.assertEqual(flow.phase,'review_required')
        self.assertNotIn('provision_requested',flow.events)

    def test_all_demo_outcomes_are_explicitly_simulated(self):
        for mode,phase in [('paid','delivered'),('pending','awaiting_payment'),('mismatch','review_required'),('timeout','review_required')]:
            result=run_demo(TENANT_A,BOT_A,'synthetic-customer','basic',mode)
            self.assertTrue(result['simulation']);self.assertFalse(result['live_actions'])
            self.assertEqual(result['phase'],phase)
            self.assertEqual(bool(result['demo_delivery']),mode=='paid')


class ReadOnlyPreviewDB(FakeDB):
    def execute(self,query,args=()):
        sql=' '.join(query.split())
        if not sql.startswith(('SELECT tu.role','SELECT id,telegram_bot_id')):
            raise AssertionError('Simulation attempted persistence or credential access')
        return super().execute(query,args)
    def commit(self):raise AssertionError('Simulation must never commit')


class ServicePreviewApiTests(unittest.TestCase):
    def setUp(self):
        self.stack=ExitStack();self.db=ReadOnlyPreviewDB()
        app.dependency_overrides[get_connection]=lambda:self.db
        self.stack.enter_context(patch.dict(os.environ,{'TELBOT_ENV':'uat','TELBOT_MANAGER_TOKEN':'111:TESTTOKEN','TELBOT_REPLIES_ENABLED':'true','TELBOT_EXTERNAL_API_ENABLED':'true'}))
        for target in ['experiments.telegram_bot_builder.reply_runtime.send_text','experiments.telegram_bot_builder.reply_runtime.invoke_api','experiments.telegram_bot_builder.vault.TokenVault.decrypt']:
            self.stack.enter_context(patch(target,side_effect=AssertionError('Live operation forbidden in simulation')))
        self.client=TestClient(app);self.url=f'/api/v1/tenants/{TENANT_A}/bots/{BOT_A}/service-flow-preview'
        self.headers={'X-Telegram-Init-Data':signed_initdata()}
    def tearDown(self):app.dependency_overrides.clear();self.client.close();self.stack.close()
    def test_preview_is_owner_editor_surface_without_live_effects(self):
        for mode in ['paid','pending','mismatch','timeout']:
            r=self.client.post(self.url,headers=self.headers,json={'plan_id':'basic','scenario':mode})
            self.assertEqual(r.status_code,200,r.text);self.assertTrue(r.json()['simulation']);self.assertFalse(r.json()['live_actions'])
        self.assertEqual(self.db.commits,0)
    def test_auth_scope_and_validation_do_not_echo_credentials(self):
        body={'plan_id':'basic','scenario':'paid'}
        self.assertEqual(self.client.post(self.url,json=body).status_code,401)
        self.assertEqual(self.client.post(self.url,headers={'X-Telegram-Init-Data':signed_initdata(user_id=111222)},json=body).status_code,403)
        self.assertEqual(self.client.post(f'/api/v1/tenants/{TENANT_B}/bots/{BOT_A}/service-flow-preview',headers=self.headers,json=body).status_code,403)
        self.assertEqual(self.client.post(f'/api/v1/tenants/{TENANT_A}/bots/{BOT_B}/service-flow-preview',headers=self.headers,json=body).status_code,404)
        result=self.client.post(self.url,headers=self.headers,json={**body,'credential':'SYNTHETIC-PRIVATE'})
        self.assertEqual(result.status_code,422);self.assertNotIn('SYNTHETIC-PRIVATE',result.text)
