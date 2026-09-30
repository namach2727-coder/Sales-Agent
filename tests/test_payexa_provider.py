import httpx
import pytest

from app.config import Settings
from app.commerce.payexa_provider import PayexaClient, PayexaCreateUnknown, PayexaError


def client(handler):
    # Only synthetic credentials are used in this isolated transport.
    settings = Settings(_env_file=None, payexa_api_key='fake-test-key')
    return PayexaClient(settings, client=httpx.Client(base_url=settings.payexa_base_url, headers={'X-API-KEY':'fake-test-key'}, transport=httpx.MockTransport(handler)))


def test_create_precision_and_private_fields(caplog):
    def handler(request):
        assert request.headers['X-API-KEY'] == 'fake-test-key'
        assert request.url.path == '/v1/payment/request'
        return httpx.Response(201, text='{"authority":"SAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA","order_id":"ORD-AAAAAAAAAAAAAAAA","amount_unique":249111.000000000000000001,"card_number":"private-card"}')
    result = client(handler).create_transaction(amount=250000, callback_url='https://example.com/callback', order_ref='test')
    assert result.verification_token == '249111.000000000000000001'
    assert result.payment_url.startswith('https://sandbox.pexn.ir/startPay?authority=')
    assert '249111' not in repr(result)
    assert 'private-card' not in repr(result) + caplog.text


@pytest.mark.parametrize('code', [200, 201, 400, 404, 409])
def test_exact_verify_http_contract(code):
    def handler(request):
        assert b'249111.0' in request.content
        return httpx.Response(code, json={'status':'SUCCESS','merchant_verified':True})
    assert client(handler).verify_transaction(order_id='ORD-AAAAAAAAAAAAAAAA', token='249111.0').http_status == code


@pytest.mark.parametrize('body', ['{}','{"authority":"bad"}', '{"authority":"SAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA","order_id":"bad"}'])
def test_invalid_successful_create_is_ambiguous(body):
    with pytest.raises(PayexaCreateUnknown):
        client(lambda request: httpx.Response(201,text=body)).create_transaction(amount=1,callback_url='https://example.com',order_ref='test')


def test_transport_never_exposes_body_or_key():
    def handler(request):
        raise httpx.ReadTimeout('fake-test-key private-card',request=request)
    with pytest.raises(PayexaCreateUnknown) as error:
        client(handler).create_transaction(amount=1,callback_url='https://example.com',order_ref='test')
    assert 'fake-test-key' not in str(error.value)
    with pytest.raises(PayexaError):
        client(handler).verify_transaction(order_id='test',token='secret-test-token')


def test_status_success_is_only_data():
    assert client(lambda request: httpx.Response(200,json={'status':'SUCCESS','paid_at':None})).get_status(order_id='test') == {'status':'SUCCESS','paid_at':None}


def test_constructed_client_sends_configured_header(monkeypatch):
    constructed = {}
    class TransportClient:
        def __init__(self, **kwargs):
            constructed.update(kwargs)
    monkeypatch.setattr('app.commerce.payexa_provider.httpx.Client', TransportClient)
    PayexaClient(Settings(_env_file=None,payexa_api_key='synthetic-only'))
    assert constructed['headers'] == {'X-API-KEY':'synthetic-only'}
    assert constructed['follow_redirects'] is False


@pytest.mark.parametrize('code,exception', [(400,PayexaError),(500,PayexaCreateUnknown)])
def test_creation_rejection_vs_unknown(code,exception):
    with pytest.raises(exception):
        client(lambda request:httpx.Response(code)).create_transaction(amount=1,callback_url='https://example.com',order_ref='test')


def test_invalid_verify_success_does_not_become_paid():
    with pytest.raises(PayexaError):
        client(lambda request:httpx.Response(200,json={'status':'SUCCESS','merchant_verified':'true'})).verify_transaction(order_id='test',token='test')
