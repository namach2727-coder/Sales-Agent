import asyncio
import os
from unittest.mock import patch
import httpx
from .reply_runtime import send_text, process_reply


def test_successful_transport():
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json={'ok': True, 'result': {'message_id': 7}}))
    assert asyncio.run(send_text('synthetic', {'chat_id': 1, 'text': 'hello'}, transport=transport)) == (7, None)


def test_timeout_is_uncertain_without_secret():
    def timeout(request):
        raise httpx.ReadTimeout('secret-bearing upstream URL', request=request)
    assert asyncio.run(send_text('synthetic', {}, transport=httpx.MockTransport(timeout))) == (None, 'delivery_unknown')


def test_rejected_transport():
    transport = httpx.MockTransport(lambda r: httpx.Response(429, json={'ok': False}))
    assert asyncio.run(send_text('synthetic', {}, transport=transport)) == (None, 'telegram_rejected')


def test_disabled_runtime_never_touches_database():
    with patch.dict(os.environ, {'TELBOT_ENV': 'uat', 'TELBOT_REPLIES_ENABLED': 'false'}):
        asyncio.run(process_reply(None, None, None, None))


def test_non_uat_runtime_never_touches_database():
    with patch.dict(os.environ, {'TELBOT_ENV': 'production', 'TELBOT_REPLIES_ENABLED': 'true'}):
        asyncio.run(process_reply(None, None, None, None))
