"""UAT private replies with durable at-most-once attempts (no uncertain retries)."""
import os
import httpx
try:
    from .core import BotConfiguration, ReplyRule, is_start_command, keyword_matches
    from .reply_planner import plan_private_reply, reply_keyboard
    from .vault import TokenVault, CredentialError
    from .builder_storage import read_rules
    from .api_actions import open_call, invoke_api, ApiActionError
except ImportError:
    from core import BotConfiguration, ReplyRule, is_start_command, keyword_matches
    from reply_planner import plan_private_reply, reply_keyboard
    from vault import TokenVault, CredentialError
    from builder_storage import read_rules
    from api_actions import open_call, invoke_api, ApiActionError


async def send_text(token, payload, *, transport=None):
    """Return categorical outcomes only; never propagate credential-bearing errors."""
    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=False, transport=transport) as client:
            response = await client.post('https://api.telegram.org/bot' + token + '/sendMessage', json=payload)
        data = response.json()
        result = data.get('result') if isinstance(data, dict) else None
        mid = result.get('message_id') if isinstance(result, dict) else None
        if response.status_code == 200 and isinstance(data, dict) and data.get('ok') is True and type(mid) is int and mid > 0:
            return mid, None
        return None, 'telegram_rejected'
    except (httpx.HTTPError, ValueError, TypeError):
        return None, 'delivery_unknown'


def reserve_api_budget(db, tenant, bot_id):
    """Serialize a small per-bot budget; store only aggregate audit metadata."""
    lock = db.execute("SELECT pg_try_advisory_xact_lock(hashtextextended(%s,0)) AS acquired", ('telbot-api:' + str(bot_id),)).fetchone()
    if not lock or not lock['acquired']:
        db.commit()
        return False
    used = db.execute("""SELECT count(*) AS n FROM telbot.audit_events
        WHERE tenant_id=%s AND bot_id=%s AND event_type='api_action_attempt'
          AND created_at>=now()-interval '1 minute'""", (tenant, bot_id)).fetchone()
    allowed = int(used['n']) < 20
    if allowed:
        db.execute("""INSERT INTO telbot.audit_events(tenant_id,bot_id,event_type)
            VALUES (%s,%s,'api_action_attempt')""", (tenant, bot_id))
    db.commit()
    return allowed


async def process_reply(db, bot, update, inbound_id):
    if os.getenv('TELBOT_ENV') != 'uat' or os.getenv('TELBOT_REPLIES_ENABLED') != 'true':
        return
    tenant, bid = bot['tenant_id'], bot['id']
    # Serialize the decision/attempt reservation with pause, not the network call.
    # A receipt observed while paused stays suppressed even if resume races ahead.
    state = {'status':'paused'} if bot.get('status') == 'paused' else db.execute(
        "SELECT status FROM telbot.bots WHERE tenant_id=%s AND id=%s FOR SHARE", (tenant,bid)).fetchone()
    if not state or state['status'] != 'active':
        if state and state['status'] == 'paused':
            db.execute("""UPDATE telbot.inbound_updates SET processing_status='ignored',processed_at=now()
                WHERE id=%s AND tenant_id=%s AND bot_id=%s""", (inbound_id,tenant,bid))
            db.commit()
        return
    config = db.execute("""SELECT id,greeting,fallback_reply FROM telbot.configuration_versions
        WHERE tenant_id=%s AND bot_id=%s AND state='published' LIMIT 1""", (tenant, bid)).fetchone()
    if not config:
        return
    rules = [rule for rule in read_rules(db, tenant, config['id']) if rule.get('enabled', True)]
    cfg = BotConfiguration(str(tenant), update['_bot_id'], config['greeting'], config['fallback_reply'], tuple(ReplyRule(r['keyword'], r['response_text'], r['match_mode']) for r in rules))
    payload = plan_private_reply(cfg, update, tenant_id=str(tenant), bot_id=update['_bot_id'])
    if payload is None:
        return
    payload['reply_markup'] = reply_keyboard(rules)
    try:
        token = TokenVault(os.getenv('TELBOT_TOKEN_FERNET_KEY', '')).decrypt(bytes(bot['credential_ciphertext']))
    except (CredentialError, TypeError):
        return
    if token.split(':', 1)[0] != str(update['_bot_id']):
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
    # The committed attempt covers BOTH the optional API action and Telegram send.
    # Replayed inbound updates must never repeat a POST to a customer API.
    api_error = None
    if not is_start_command(update['message']['text']):
        matched = next((r for r in rules if keyword_matches(r['keyword'], r['match_mode'], update['message']['text'])), None)
        if matched and matched.get('action_type') == 'api':
            if os.getenv('TELBOT_EXTERNAL_API_ENABLED') == 'true' and reserve_api_budget(db, tenant, bid):
                try:
                    value = open_call(matched['api_request_ciphertext'], os.getenv('TELBOT_TOKEN_FERNET_KEY', ''))
                    payload['text'] = await invoke_api(value, update['message']['text'])
                except ApiActionError as exc:
                    api_error = str(exc)
            else:
                api_error = 'api_actions_disabled' if os.getenv('TELBOT_EXTERNAL_API_ENABLED') != 'true' else 'api_rate_limited'
            # Persist the actual outgoing text or configured failure response before sending.
            db.execute("""UPDATE telbot.outbound_messages SET response_text=%s,error_code=%s
                WHERE id=%s AND tenant_id=%s AND bot_id=%s""",
                (payload['text'], api_error, outbound['id'], tenant, bid))
            db.commit()
    mid, error = await send_text(token, payload)
    db.execute("""UPDATE telbot.outbound_messages SET delivery_status=%s,
        telegram_message_id=%s,error_code=%s,sent_at=CASE WHEN %s THEN now() ELSE NULL END
        WHERE id=%s AND tenant_id=%s AND bot_id=%s""", ('sent' if mid else 'failed',mid,error or api_error,bool(mid),outbound['id'],tenant,bid))
    db.execute("""UPDATE telbot.inbound_updates SET processing_status=%s,processed_at=now()
        WHERE id=%s AND tenant_id=%s AND bot_id=%s""", ('processed' if mid else 'failed',inbound_id,tenant,bid))
    db.commit()
