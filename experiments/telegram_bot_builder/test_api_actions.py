import asyncio
import json
import ssl
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from cryptography.fernet import Fernet
from pydantic import ValidationError
from experiments.telegram_bot_builder.api_actions import (
    ApiActionError, ApiCallInput, PublicHTTPTransport, PublicNetworkBackend,
    extract_reply, invoke_api, is_public_address, materialize_call, open_call,
    public_call, resolve_public_addresses, seal_call, validate_endpoint,
)


def response(data, code=200, headers=None):
    return httpx.Response(code, headers=headers or {'Content-Type': 'application/json'},
        stream=httpx.ByteStream(json.dumps(data).encode()))


class ActionValidationTests(unittest.TestCase):
    def test_only_public_https_domain_shapes(self):
        for url in ['http://api.example.com', 'https://127.0.0.1/a', 'https://[::1]',
                    'https://api.example.com:444/a', 'https://user:password@api.example.com',
                    'https://api.example.com/a?secret=x', 'https://api.example.com/#x',
                    'https://api.example.com\\@evil.com', 'https://metadata.google.internal/a',
                    'https://localhost', ' https://api.example.com']:
            with self.subTest(url=url), self.assertRaises(ValueError): validate_endpoint(url)
        self.assertEqual(validate_endpoint('https://api.example.com/lookup'), 'https://api.example.com/lookup')

    def test_non_public_and_mapped_destinations(self):
        for address in ['127.0.0.1', '10.0.0.1', '169.254.169.254', '0.0.0.0', '::1',
                        'fc00::1', 'fe80::1', '224.0.0.1', '::ffff:8.8.8.8', '192.0.2.1']:
            self.assertFalse(is_public_address(address), address)
        self.assertTrue(is_public_address('8.8.8.8'))

    def test_header_and_body_bounds(self):
        for settings in [dict(auth_mode='header', auth_header='Host'), dict(auth_mode='header', auth_header='X-Forwarded-Host'),
                         dict(method='GET', json_body={'x': 1}), dict(params={'x': 'a' * 1025}),
                         dict(response_path='data.__bad[0]'), dict(method='POST', json_body={'x': 'a' * 8193}),
                         dict(credential='bad\nsecret')]:
            with self.subTest(settings=list(settings)), self.assertRaises(ValidationError):
                ApiCallInput(url='https://api.example.com', **settings)

    def test_vault_round_trip_and_no_readback(self):
        key = Fernet.generate_key().decode()
        value = materialize_call(ApiCallInput(url='https://api.example.com', auth_mode='bearer', credential='synthetic-key'))
        sealed = seal_call(value, key)
        self.assertNotIn(b'synthetic-key', sealed)
        self.assertEqual(open_call(sealed, key), value)
        self.assertNotIn('credential', public_call(value))
        self.assertTrue(public_call(value)['credential_present'])
        with self.assertRaises(ApiActionError): open_call(sealed, Fernet.generate_key().decode())

    def test_preserve_secret_only_same_endpoint_and_auth(self):
        original = materialize_call(ApiCallInput(url='https://api.example.com/a', auth_mode='bearer', credential='synthetic'))
        retained = materialize_call(ApiCallInput(url='https://api.example.com/a', auth_mode='bearer'), original)
        self.assertEqual(retained['credential'], 'synthetic')
        for url in ['https://other.example.com/a', 'https://api.example.com/b']:
            with self.assertRaises(ApiActionError): materialize_call(ApiCallInput(url=url, auth_mode='bearer'), original)
        self.assertEqual(materialize_call(ApiCallInput(url='https://api.example.com/a'), original)['credential'], '')

    def test_path_extraction_rejects_objects_and_missing(self):
        self.assertEqual(extract_reply({'data': [{'answer': 'Hello'}]}, 'data.0.answer'), 'Hello')
        for data, path in [({}, ''), ({}, 'missing'), (None, ''), ('x' * 4097, '')]:
            with self.assertRaises(ApiActionError): extract_reply(data, path)


class NetworkTests(unittest.IsolatedAsyncioTestCase):
    async def test_mixed_dns_answers_fail_closed(self):
        with patch('asyncio.base_events.BaseEventLoop.getaddrinfo', new_callable=AsyncMock,
                return_value=[(None,None,None,None,('8.8.8.8',443)), (None,None,None,None,('127.0.0.1',443))]):
            with self.assertRaises(ApiActionError): await resolve_public_addresses('api.example.com')

    async def test_connection_is_pinned_and_original_tls_hostname_verified(self):
        writes, tls = [], []
        payload = b'{"answer":"Hello"}'
        class Stream:
            sent = False
            async def read(self, max_bytes, timeout=None):
                if self.sent: return b''
                self.sent = True
                return b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: '+str(len(payload)).encode()+b'\r\n\r\n'+payload
            async def write(self, buffer, timeout=None): writes.append(bytes(buffer))
            async def aclose(self): pass
            async def start_tls(self, ssl_context, server_hostname=None, timeout=None):
                tls.append((server_hostname, ssl_context.check_hostname, ssl_context.verify_mode)); return self
            def get_extra_info(self, name): return None
        backend = PublicNetworkBackend('api.example.com')
        backend.backend.connect_tcp = AsyncMock(return_value=Stream())
        transport = PublicHTTPTransport('api.example.com'); transport.pool._network_backend = backend
        with patch('experiments.telegram_bot_builder.api_actions.resolve_public_addresses', new_callable=AsyncMock, return_value=['8.8.8.8']):
            result = await invoke_api({'url':'https://api.example.com/a', 'response_path':'answer'}, 'hello', transport=transport)
        self.assertEqual(result, 'Hello')
        self.assertEqual(backend.backend.connect_tcp.call_args.args, ('8.8.8.8', 443))
        self.assertEqual(tls, [('api.example.com', True, ssl.CERT_REQUIRED)])
        self.assertIn(b'Host: api.example.com', b''.join(writes))

    async def test_get_and_post_send_only_opted_in_text(self):
        calls = []
        def handle(request):
            calls.append(request); return response({'data': {'answer':'OK'}})
        for method, include in [('GET', False), ('POST', True)]:
            value = {'url':'https://api.example.com/a', 'method':method, 'response_path':'data.answer',
                'include_message':include, 'message_field':'q', 'auth_mode':'bearer', 'credential':'synthetic'}
            self.assertEqual(await invoke_api(value, 'private-input', transport=httpx.MockTransport(handle)), 'OK')
        self.assertNotIn('private-input', str(calls[0].url))
        self.assertEqual(json.loads(calls[1].content)['q'], 'private-input')
        self.assertEqual(calls[1].headers['Authorization'], 'Bearer synthetic')
        self.assertEqual(len(calls), 2)

    async def test_no_redirect_retry_raw_error_or_sensitive_response(self):
        for data, code, headers, expected in [
            ({},302,{'Location':'https://other.example.com'},'api_http_error'),
            ({},429,None,'api_http_error'),
            ({'a':'synthetic'},200,None,'api_sensitive_response'),
            ({'a':'x' * 70000},200,None,'api_response_too_large'),
            ({},200,{'Content-Type':'text/html'},'api_response_not_json')]:
            calls = []
            def handle(request): calls.append(request); return response(data, code, headers)
            with self.subTest(expected=expected), self.assertRaisesRegex(ApiActionError, expected):
                await invoke_api({'url':'https://api.example.com/a', 'response_path':'a',
                    'auth_mode':'bearer','credential':'synthetic'}, 'hello', transport=httpx.MockTransport(handle))
            self.assertEqual(len(calls), 1)

    async def test_timeout_is_categorical_and_not_retried(self):
        calls=[]
        def handle(request): calls.append(1); raise httpx.ReadTimeout('raw credential-bearing URL', request=request)
        with self.assertRaisesRegex(ApiActionError, '^api_timeout$'):
            await invoke_api({'url':'https://api.example.com/a'}, 'x', transport=httpx.MockTransport(handle))
        self.assertEqual(len(calls), 1)
