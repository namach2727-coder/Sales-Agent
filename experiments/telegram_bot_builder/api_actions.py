"""Versioned, encrypted HTTP/JSON actions. Never return credentials or raw errors."""
from __future__ import annotations
import asyncio
import ipaddress
import json
import re
import socket
import ssl
from typing import Any, Literal

import httpx
from cryptography.fernet import Fernet, InvalidToken
from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator


class ApiActionError(ValueError):
    """Only static public error codes may cross this boundary."""


def validate_endpoint(raw: str) -> str:
    if any(ord(c) < 33 for c in raw) or '\\' in raw:
        raise ValueError('Invalid HTTPS endpoint')
    try:
        url = httpx.URL(raw)
        host = url.host
        if (url.scheme != 'https' or url.port not in (None, 443) or url.userinfo
                or url.query or url.fragment or not host or len(host) > 253
                or not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}', host)
                or host.endswith(('.localhost', '.local', '.internal', '.test'))):
            raise ValueError('Invalid HTTPS endpoint')
        return str(url)
    except (httpx.InvalidURL, UnicodeError):
        raise ValueError('Invalid HTTPS endpoint') from None


class ApiCallInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    url: str = Field(min_length=8, max_length=2048)
    method: Literal['GET', 'POST'] = 'GET'
    params: dict[str, str] = Field(default_factory=dict, max_length=20)
    json_body: dict[str, Any] = Field(default_factory=dict)
    include_message: bool = False
    message_field: str = Field(default='message', pattern=r'^[A-Za-z_][A-Za-z0-9_]{0,63}$')
    response_path: str = Field(default='', max_length=200)
    auth_mode: Literal['none', 'bearer', 'header'] = 'none'
    auth_header: str = Field(default='X-API-Key', max_length=64)
    credential: SecretStr | None = Field(default=None, max_length=2048)

    @model_validator(mode='after')
    def validate_call(self):
        self.url = validate_endpoint(self.url)
        if self.response_path and not re.fullmatch(r'[\w-]+(?:\.[\w-]+){0,9}', self.response_path):
            raise ValueError('Invalid JSON response path')
        if self.auth_mode == 'header' and not re.fullmatch(r'X-(?!Forwarded)[A-Za-z0-9-]{1,60}', self.auth_header, re.I):
            raise ValueError('Use an X- API credential header')
        if self.method == 'GET' and self.json_body:
            raise ValueError('GET cannot have a JSON body')
        if any(len(k) > 64 or len(v) > 1024 or not k for k, v in self.params.items()):
            raise ValueError('Invalid API parameters')
        def check(value, depth=0):
            if depth > 6: raise ValueError('API body too deep')
            if isinstance(value, dict):
                for key, item in value.items():
                    if not isinstance(key, str): raise ValueError('Invalid JSON key')
                    check(item, depth + 1)
            elif isinstance(value, list):
                for item in value: check(item, depth + 1)
        check(self.json_body)
        if len(json.dumps(self.json_body, ensure_ascii=False, allow_nan=False).encode()) > 8192:
            raise ValueError('API body too large')
        secret = self.credential.get_secret_value() if self.credential else ''
        if '\r' in secret or '\n' in secret:
            raise ValueError('Invalid API credential')
        return self


def materialize_call(call: ApiCallInput, previous: dict | None = None) -> dict:
    value = call.model_dump(exclude={'credential'})
    secret = call.credential.get_secret_value() if call.credential else ''
    if call.auth_mode != 'none' and not secret:
        # Never send a stored credential to a different origin or auth mechanism.
        same = previous and all(previous.get(k) == value.get(k) for k in ('url', 'auth_mode', 'auth_header'))
        if not same or not previous.get('credential'):
            raise ApiActionError('api_credential_required')
        secret = previous['credential']
    value['credential'] = secret if call.auth_mode != 'none' else ''
    return value


def seal_call(value: dict, key: str) -> bytes:
    try:
        raw = b'telbot-api-v1\0' + json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
        if len(raw) > 32768: raise ValueError()
        return Fernet(key.encode('ascii')).encrypt(raw)
    except (ValueError, TypeError, UnicodeError):
        raise ApiActionError('api_vault_unavailable') from None


def open_call(ciphertext: bytes, key: str) -> dict:
    try:
        raw = Fernet(key.encode('ascii')).decrypt(bytes(ciphertext))
        if not raw.startswith(b'telbot-api-v1\0'): raise ValueError()
        value = json.loads(raw[len(b'telbot-api-v1\0'):])
        if not isinstance(value, dict): raise ValueError()
        ApiCallInput(**value)  # Reject corrupt/obsolete settings before network use.
        return value
    except (InvalidToken, ValueError, TypeError, UnicodeError):
        raise ApiActionError('api_vault_unavailable') from None


def public_call(value: dict) -> dict:
    return {**{k: v for k, v in value.items() if k != 'credential'},
            'credential_present': bool(value.get('credential'))}


def is_public_address(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
        return (ip.is_global and not any((ip.is_multicast, ip.is_reserved, ip.is_loopback,
                ip.is_link_local, ip.is_unspecified)) and not getattr(ip, 'ipv4_mapped', None)
                and not getattr(ip, 'sixtofour', None) and not getattr(ip, 'teredo', None)
                and not (isinstance(ip, ipaddress.IPv6Address) and (ip in ipaddress.ip_network('64:ff9b::/96') or ip in ipaddress.ip_network('64:ff9b:1::/48'))))
    except ValueError:
        return False


async def resolve_public_addresses(host: str) -> list[str]:
    try:
        answers = await asyncio.wait_for(asyncio.get_running_loop().getaddrinfo(
            host, 443, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM), timeout=3)
    except (OSError, TimeoutError):
        raise ApiActionError('api_dns_unavailable') from None
    addresses = list(dict.fromkeys(answer[4][0] for answer in answers))
    if not addresses or not all(is_public_address(ip) for ip in addresses):
        raise ApiActionError('api_destination_blocked')
    return addresses


class PublicNetworkBackend:
    """Pin each connection to validated IPs; TLS still verifies original hostname."""
    def __init__(self, host: str):
        from httpcore._backends.anyio import AnyIOBackend
        self.backend = AnyIOBackend()
        self.host = host

    async def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        if host != self.host or port != 443:
            raise ApiActionError('api_destination_blocked')
        addresses = await resolve_public_addresses(host)
        # No application request has been sent during connection establishment.
        return await self.backend.connect_tcp(addresses[0], port, timeout=timeout,
            local_address=local_address, socket_options=socket_options)

    async def connect_unix_socket(self, *args, **kwargs):
        raise ApiActionError('api_destination_blocked')

    async def sleep(self, seconds):
        await asyncio.sleep(seconds)


class PublicHTTPTransport(httpx.AsyncBaseTransport):
    def __init__(self, host):
        import httpcore
        self.pool = httpcore.AsyncConnectionPool(ssl_context=ssl.create_default_context(),
            max_connections=1, max_keepalive_connections=0, retries=0,
            network_backend=PublicNetworkBackend(host))

    async def handle_async_request(self, request):
        import httpcore
        class Body(httpx.AsyncByteStream):
            def __init__(self, stream): self.stream = stream
            async def __aiter__(self):
                async for chunk in self.stream: yield chunk
            async def aclose(self): await self.stream.aclose()
        response = await self.pool.handle_async_request(httpcore.Request(
            method=request.method, url=httpcore.URL(scheme=request.url.raw_scheme,
                host=request.url.raw_host, port=request.url.port, target=request.url.raw_path),
            headers=request.headers.raw, content=request.stream, extensions=request.extensions))
        return httpx.Response(response.status, headers=response.headers,
            stream=Body(response.stream), extensions=response.extensions)

    async def aclose(self):
        await self.pool.aclose()


def extract_reply(data: Any, path: str) -> str:
    value = data
    for part in path.split('.') if path else []:
        if isinstance(value, dict) and part in value: value = value[part]
        elif isinstance(value, list) and part.isdecimal() and int(part) < len(value): value = value[int(part)]
        else: raise ApiActionError('api_response_path_missing')
    if value is None or not isinstance(value, (str, int, float, bool)):
        raise ApiActionError('api_response_not_text')
    text = value if isinstance(value, str) else json.dumps(value, allow_nan=False)
    if not text.strip() or len(text) > 4096: raise ApiActionError('api_response_not_text')
    return text


async def invoke_api(value: dict, message: str, *, transport=None) -> str:
    """Single bounded request. No redirects, proxies, retries, cookies or raw errors."""
    import httpcore
    try:
        validated = ApiCallInput(**value)
        endpoint = validated.url
        params, body = dict(validated.params), dict(validated.json_body)
        if validated.include_message:
            (params if validated.method == 'GET' else body)[validated.message_field] = message
        headers = {'Accept': 'application/json', 'Accept-Encoding': 'identity'}
        secret = value.get('credential', '')
        if validated.auth_mode == 'bearer': headers['Authorization'] = 'Bearer ' + secret
        if validated.auth_mode == 'header': headers[validated.auth_header] = secret
        if validated.auth_mode != 'none' and not secret: raise ApiActionError('api_credential_required')
        async with asyncio.timeout(8):
            async with httpx.AsyncClient(timeout=5, follow_redirects=False, trust_env=False,
                    transport=transport or PublicHTTPTransport(httpx.URL(endpoint).host)) as client:
                async with client.stream(validated.method, endpoint, params=params, headers=headers,
                        **({'json': body} if validated.method == 'POST' else {})) as response:
                    if response.status_code < 200 or response.status_code >= 300:
                        raise ApiActionError('api_http_error')
                    if response.headers.get('content-encoding', 'identity').lower() != 'identity':
                        raise ApiActionError('api_response_encoding')
                    if response.headers.get('content-type', '').split(';')[0].strip().lower() not in ('application/json', 'application/problem+json'):
                        raise ApiActionError('api_response_not_json')
                    raw = bytearray()
                    async for chunk in response.aiter_raw():
                        raw.extend(chunk)
                        if len(raw) > 65536: raise ApiActionError('api_response_too_large')
        text = extract_reply(json.loads(raw), validated.response_path)
        if secret and secret in text: raise ApiActionError('api_sensitive_response')
        return text
    except ApiActionError:
        raise
    except (TimeoutError, httpx.TimeoutException, httpcore.TimeoutException):
        raise ApiActionError('api_timeout') from None
    except (httpx.HTTPError, httpcore.NetworkError, httpcore.ProtocolError, OSError, ValueError, TypeError, UnicodeError):
        raise ApiActionError('api_unavailable') from None
