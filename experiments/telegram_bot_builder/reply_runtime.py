"""UAT private replies with durable at-most-once attempts (no uncertain retries)."""
import os
import httpx
try:
    from .core import BotConfiguration, ReplyRule
    from .reply_planner import plan_private_reply
    from .vault import TokenVault, CredentialError
except ImportError:
    from core import BotConfiguration, ReplyRule
    from reply_planner import plan_private_reply
    from vault import TokenVault, CredentialError


async def send_text(token, payload, *, transport=None):
    """Return categorical outcomes only; never propagate credential-bearing errors."""
    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=False, transport=transport) as client:
            response = await client.post('https://api.telegram.org/bot' + token + '/sendMessage', json=payload)
        data = response.json()
        result = data.get('result') if isinstance(data, dict) else None
        mid = result.get('message_id') if isinstance(result, dict) else None
        if response.status_code == 200 and data.get('ok') is True and type(mid) is int and mid > 0:
            return mid, None
        return None, 'telegram_rejected'
    except (httpx.HTTPError, ValueError, TypeError):
        return None, 'delivery_unknown'


async def process_reply(db, bot, update, inbound_id):
    if os.getenv('TELBOT_ENV') != 'uat' or os.getenv('TELBOT_REPLIES_ENABLED') != 'true':
        return
    tenant, bid = bot['tenant_id'], bot['id']
    config = db.execute("""SELECT id,greeting,fallback_reply FROM telbot.configuration_versions
        WHERE tenant_id=%s AND bot_id=%s AND state='published' LIMIT 1""", (tenant, bid)).fetchone()
    if not config:
        return
    rules = db.execute("""SELECT keyword,response_text,match_mode FROM telbot.reply_rules
        WHERE tenant_id=%s AND configuration_id=%s AND enabled=true ORDER BY priority LIMIT 100""", (tenant, config['id'])).fetchall()
    cfg = BotConfiguration(str(tenant), update['_bot_id'], config['greeting'], config['fallback_reply'], tuple(ReplyRule(r['keyword'], r['response_text'], r['match_mode']) for r in rules))
    payload = plan_private_reply(cfg, update, tenant_id=str(tenant), bot_id=update['_bot_id'])
    if payload is None:
        return
    try:
        token = TokenVault(os.getenv('TELBOT_TOKEN_FERNET_KEY', '')).decrypt(bytes(bot['credential_ciphertext']))
    except (CredentialError, TypeError):
        return
    # Inbound insertion is unique. Only its winning request calls this function.
    # Persist attempts BEFORE network: a timeout/crash must never trigger a blind resend.
    session = db.execute("""INSERT INTO telbot.chat_sessions(tenant_id,bot_id,telegram_chat_id)
        VALUES (%s,%s,%s) ON CONFLICT (bot_id,telegram_chat_id)
        DO UPDATE SET last_activity_at=now() RETURNING id,status""", (tenant, bid, payload['chat_id'])).fetchone()
    if session['status'] != 'open':
        return
    outbound = db.execute("""INSERT INTO telbot.outbound_messages
        (tenant_id,bot_id,session_id,source_update_id,response_text,attempts,error_code)
        VALUES (%s,%s,%s,%s,%s,1,'delivery_unknown') RETURNING id""", (tenant,bid,session['id'],inbound_id,payload['text'])).fetchone()
    db.commit()
    mid, error = await send_text(token, payload)
    db.execute("""UPDATE telbot.outbound_messages SET delivery_status=%s,
        telegram_message_id=%s,error_code=%s,sent_at=CASE WHEN %s THEN now() ELSE NULL END
        WHERE id=%s AND tenant_id=%s AND bot_id=%s""", ('sent' if mid else 'failed',mid,error,bool(mid),outbound['id'],tenant,bid))
    db.execute("""UPDATE telbot.inbound_updates SET processing_status=%s,processed_at=now()
        WHERE id=%s AND tenant_id=%s AND bot_id=%s""", ('processed' if mid else 'failed',inbound_id,tenant,bid))
    db.commit()
