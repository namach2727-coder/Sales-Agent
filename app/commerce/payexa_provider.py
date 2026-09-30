"""Payexa HTTP boundary; provider bodies and verification tokens stay private."""
from dataclasses import dataclass, field
from decimal import Decimal
import json
import re
from urllib.parse import urlencode, urlsplit

import httpx

from app.config import Settings


class PayexaError(Exception):
    pass


class PayexaConfigurationError(PayexaError):
    pass


class PayexaCreateUnknown(PayexaError):
    pass


@dataclass(frozen=True)
class PayexaCreateResult:
    transaction_id: str
    authority: str
    verification_token: str = field(repr=False)
    payment_url: str


@dataclass(frozen=True)
class PayexaVerifyResult:
    http_status: int
    status: str


class PayexaClient:
    def __init__(self, settings: Settings, *, client=None):
        base = settings.payexa_base_url.rstrip('/')
        url = urlsplit(base)
        key = settings.payexa_api_key.get_secret_value().strip()
        if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment or url.path or not key:
            raise PayexaConfigurationError('Payexa configuration is unavailable')
        self._base = base
        self._client = client or httpx.Client(base_url=base, timeout=settings.payexa_timeout_seconds, headers={'X-API-KEY': key}, follow_redirects=False)

    def close(self):
        self._client.close()

    @staticmethod
    def _body(response):
        try:
            body = json.loads(response.text, parse_float=Decimal)
            if not isinstance(body, dict):
                raise ValueError()
            return body
        except (ValueError, TypeError):
            raise PayexaError('Payexa response is invalid') from None

    def create_transaction(self, *, amount: int, callback_url: str, order_ref: str):
        try:
            response = self._client.post('/v1/payment/request', json={'amount': amount, 'callback_url': callback_url, 'meta': {'order_ref': order_ref}})
        except httpx.RequestError:
            raise PayexaCreateUnknown('Payexa creation outcome is unknown') from None
        if response.status_code != 201:
            if response.status_code >= 500 or response.status_code in (408, 429) or 200 <= response.status_code < 400:
                raise PayexaCreateUnknown('Payexa creation outcome is unknown')
            raise PayexaError('Payexa rejected creation')
        try:
            body = self._body(response)
            authority, order_id = body.get('authority'), body.get('order_id')
            token = body.get('amount_unique')
            if not isinstance(authority, str) or not re.fullmatch(r'[A-Z0-9]{32,33}', authority):
                raise ValueError()
            if not isinstance(order_id, str) or not re.fullmatch(r'ORD-[A-F0-9]{16}', order_id):
                raise ValueError()
            if isinstance(token, bool) or not isinstance(token, (Decimal, int, str)):
                raise ValueError()
            token = str(token)
            if len(token) > 128 or not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?', token):
                raise ValueError()
            return PayexaCreateResult(order_id, authority, token, self._base + '/startPay?' + urlencode({'authority': authority}))
        except (PayexaError, ValueError, TypeError):
            raise PayexaCreateUnknown('Payexa creation response is incomplete') from None

    def verify_transaction(self, *, order_id: str, token: str):
        try:
            response = self._client.post('/v1/payment/verify', json={'order_id': order_id, 'token': token})
        except httpx.RequestError:
            raise PayexaError('Payexa verification is temporarily unavailable') from None
        if response.status_code in (400, 404, 409):
            return PayexaVerifyResult(response.status_code, {400:'INVALID_TOKEN',404:'NOT_FOUND',409:'NOT_SETTLED'}[response.status_code])
        if response.status_code not in (200, 201):
            raise PayexaError('Payexa verification is unavailable')
        body = self._body(response)
        if body.get('status') != 'SUCCESS' or body.get('merchant_verified') is not True:
            raise PayexaError('Payexa verification response is invalid')
        return PayexaVerifyResult(response.status_code, 'SUCCESS')

    def get_status(self, *, order_id: str):
        try:
            response = self._client.get('/v1/payment/status', params={'order_id': order_id})
        except httpx.RequestError:
            raise PayexaError('Payexa status is unavailable') from None
        if response.status_code != 200:
            raise PayexaError('Payexa status is unavailable')
        body = self._body(response)
        if not isinstance(body.get('status'), str) or not re.fullmatch(r'[A-Z_]{1,100}', body['status']) or not isinstance(body.get('paid_at'), (str, type(None))):
            raise PayexaError('Payexa status response is invalid')
        return {'status': body['status'], 'paid_at': body.get('paid_at')}
