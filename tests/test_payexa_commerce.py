import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from tests.test_saas_commerce import commerce_api, register, login, create_paid_order
from app.commerce.payexa_provider import PayexaCreateResult, PayexaVerifyResult, PayexaCreateUnknown, PayexaError
from app.models import ManualPayment, PaymentCard, SubscriptionOrder, TenantSubscription, SaasPlan


class Provider:
    def __init__(self, code=200, unknown=False):
        self.code, self.unknown = code, unknown
        self.creates = self.verifies = 0
    def close(self):
        pass
    def create_transaction(self, **kwargs):
        self.creates += 1
        self.creation = kwargs
        if self.unknown:
            raise PayexaCreateUnknown('unknown')
        return PayexaCreateResult('ORD-AAAAAAAAAAAAAAAA','SAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA','249111.0','https://sandbox.pexn.ir/startPay?authority=test')
    def verify_transaction(self, **kwargs):
        self.verifies += 1
        assert kwargs == {'order_id':'ORD-AAAAAAAAAAAAAAAA','token':'249111.0'}
        if self.code == 500:
            raise PayexaError('temporarily unavailable')
        return PayexaVerifyResult(self.code, 'SUCCESS' if self.code in (200,201) else 'NOT_SETTLED')


def setup(commerce_api, monkeypatch, provider):
    client, engine, settings = commerce_api
    settings.payexa_callback_base_url = 'https://example.com'
    monkeypatch.setattr('app.commerce.router.build_payexa_provider', lambda settings: provider)
    register(client, 'payexa')
    headers = login(client, 'payexa')
    order = create_paid_order(client, headers)
    return client, engine, headers, order


@pytest.mark.parametrize('code,state', [(200,'PAID'),(201,'RECONCILIATION_REQUIRED'),(409,'VERIFY_PENDING'),(400,'FAILED'),(404,'FAILED'),(500,'VERIFY_PENDING')])
def test_callback_state_machine_and_snapshot(commerce_api, monkeypatch, code, state):
    provider = Provider(code)
    client, engine, headers, order = setup(commerce_api, monkeypatch, provider)
    first = client.post('/api/v1/payments/payexa',headers=headers,json={'order_public_id':order['public_id']})
    assert first.status_code == 201, first.text
    payment_id = first.json()['payment']['public_id']
    assert client.post('/api/v1/payments/payexa',headers=headers,json={'order_public_id':order['public_id']}).json() == first.json()
    assert provider.creates == 1
    with Session(engine) as db, db.begin():
        plan = db.scalar(select(SaasPlan).where(SaasPlan.code=='TEST_PAID'))
        plan.duration_days = 2
        plan.automation_limit = 99
    path = f'/api/v1/payments/payexa/callback/{payment_id}'
    assert client.post(path,json={'status':'SUCCESS','authority':'forged','order_id':'forged','amount_unique':'forged'},follow_redirects=False).status_code == 303
    read = client.get(f'/api/v1/payments/automated/{payment_id}',headers=headers)
    assert read.json()['operation_state'] == state
    assert '249111' not in read.text and 'provider_verification_token' not in read.text
    client.get(path+'?status=OK&authority=forged',follow_redirects=False)
    with Session(engine) as db:
        payment = db.scalar(select(ManualPayment))
        persisted = db.scalar(select(SubscriptionOrder).where(SubscriptionOrder.public_id==order['public_id']))
        subscriptions = list(db.scalars(select(TenantSubscription).where(TenantSubscription.source=='PURCHASED')))
        assert payment.provider_verification_token == '249111.0'
        assert payment.provider_amount is None and payment.provider_final_amount is None
        assert persisted.status == ('paid' if code==200 else 'pending')
        assert len(subscriptions) == (1 if code==200 else 0)
        if code==200:
            assert subscriptions[0].limits_json['automation_limit'] == 2
            assert (subscriptions[0].current_period_end-subscriptions[0].starts_at).days == 30
    if code in (200,201,400,404):
        assert provider.verifies == 1


def test_unknown_and_cross_tenant(commerce_api,monkeypatch):
    provider = Provider(unknown=True)
    client, engine, headers, order = setup(commerce_api,monkeypatch,provider)
    for _ in range(2):
        result=client.post('/api/v1/payments/payexa',headers=headers,json={'order_public_id':order['public_id']})
        assert result.json()['operation_state']=='CREATE_UNKNOWN'
    assert provider.creates==1
    register(client,'other-payexa')
    other=login(client,'other-payexa')
    assert client.post('/api/v1/payments/payexa',headers=other,json={'order_public_id':order['public_id']}).status_code==404
    assert client.get('/api/v1/payments/automated/'+result.json()['payment']['public_id'],headers=other).status_code==404
    assert client.post('/api/v1/payments/card-transfer',headers=headers,json={'order_public_id':order['public_id']}).status_code==409


def test_manual_provider_isolation(commerce_api,monkeypatch):
    provider=Provider()
    client,engine,headers,order=setup(commerce_api,monkeypatch,provider)
    assert client.post('/api/v1/payments/card-transfer',headers=headers,json={'order_public_id':order['public_id']}).status_code==201
    assert client.post('/api/v1/payments/payexa',headers=headers,json={'order_public_id':order['public_id']}).status_code==409
    assert provider.creates==0


def test_new_nullable_column_and_existing_rows_survive_migration(commerce_api):
    # The fixture is at current head. Remove evidence owned by migrations
    # newer than 0020 before exercising the historical 0020 -> 0019 boundary.
    client,engine,_settings=commerce_api
    register(client,'historical')
    headers=login(client,'historical')
    order=create_paid_order(client,headers)
    client.post('/api/v1/payments/card-transfer',headers=headers,json={'order_public_id':order['public_id']})

    with Session(engine) as db, db.begin():
        payment=db.scalar(select(ManualPayment))
        assert payment.provider_verification_token is None
        assert payment.provider=='manual_card_transfer'

        payment.payment_card_id = None
        payment.card_number_snapshot = None
        payment.account_number_snapshot = None
        payment.account_name_snapshot = None
        payment.bank_name_snapshot = None
        db.flush()

        for card in db.scalars(select(PaymentCard)).all():
            db.delete(card)

    from alembic import command
    from alembic.config import Config
    config = Config('alembic.ini')
    config.attributes['database_url'] = str(engine.url)
    command.downgrade(config, '0019_kpay_payment_gateway')
    command.upgrade(config, 'head')

    with Session(engine) as db:
        payment=db.scalar(select(ManualPayment))
        assert payment.provider_verification_token is None
        assert payment.amount == order['price_amount']


def test_failed_local_finalization_then_provider_replay_requires_reconciliation(commerce_api,monkeypatch):
    from app.commerce.payexa_service import PayexaService
    provider=Provider()
    client,engine,headers,order=setup(commerce_api,monkeypatch,provider)
    result=client.post('/api/v1/payments/payexa',headers=headers,json={'order_public_id':order['public_id']})
    payment_id=result.json()['payment']['public_id']
    original=PayexaService._activate_paid_subscription
    def fail(*args):
        raise RuntimeError('synthetic rollback')
    monkeypatch.setattr(PayexaService,'_activate_paid_subscription',fail)
    with pytest.raises(RuntimeError,match='synthetic rollback'):
        client.get(f'/api/v1/payments/payexa/callback/{payment_id}',follow_redirects=False)
    monkeypatch.setattr(PayexaService,'_activate_paid_subscription',original)
    provider.code=201
    client.get(f'/api/v1/payments/payexa/callback/{payment_id}',follow_redirects=False)
    assert client.get(f'/api/v1/payments/automated/{payment_id}',headers=headers).json()['operation_state']=='RECONCILIATION_REQUIRED'
    with Session(engine) as db:
        assert not list(db.scalars(select(TenantSubscription).where(TenantSubscription.source=='PURCHASED')))
