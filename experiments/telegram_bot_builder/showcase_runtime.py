"""Own showcase runtime. Atomic inquiry/state/attempt reservation before Telegram.

No blind send retries: unknown transport outcomes stay visible in owner inbox.
"""
import json
import os
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from cryptography.fernet import Fernet, InvalidToken
try:
    from .showcase import transition, BY_ID, HOME_ROWS
    from .vault import TokenVault, CredentialError
    from .reply_runtime import send_text
except ImportError:
    from showcase import transition, BY_ID, HOME_ROWS
    from vault import TokenVault, CredentialError
    from reply_runtime import send_text

class ShowcaseError(ValueError): pass

def seal(value):
    try:return Fernet(os.environ['TELBOT_TOKEN_FERNET_KEY'].encode()).encrypt(json.dumps(value,ensure_ascii=False).encode())
    except (KeyError,ValueError,TypeError):raise ShowcaseError('showcase_storage_unavailable') from None

def unseal(value):
    try:return json.loads(Fernet(os.environ['TELBOT_TOKEN_FERNET_KEY'].encode()).decrypt(bytes(value)))
    except (KeyError,InvalidToken,ValueError,TypeError,UnicodeError):raise ShowcaseError('showcase_storage_unavailable') from None

def keyboard(rows):
    return {'keyboard':[[{'text':t} for t in row] for row in rows], 'resize_keyboard':True,'is_persistent':True}

async def process_showcase(db, bot, update, inbound_id):
    """Return True only if this bot's explicit showcase setting owns the update."""
    if os.getenv('TELBOT_ENV')!='uat' or os.getenv('TELBOT_SHOWCASE_ENABLED')!='true':return False
    tenant,bid=bot['tenant_id'],bot['id']
    settings=db.execute('SELECT enabled FROM telbot.showcase_settings WHERE tenant_id=%s AND bot_id=%s',(tenant,bid)).fetchone()
    if not settings or not settings['enabled']:return False
    message=update.get('message') or {}; chat=message.get('chat') or {}; actor=message.get('from') or {}
    uid=actor.get('id'); text=message.get('text')
    if (chat.get('type')!='private' or type(uid) is not int or uid<=0 or chat.get('id')!=uid or actor.get('is_bot') is True
        or not isinstance(text,str) or not 1<=len(text)<=4096):return True
    if os.getenv('TELBOT_REPLIES_ENABLED')!='true' or bot.get('status')!='active':return True
    # Lock status decision vs Pause; the operation's network calls happen after commit.
    current=db.execute('SELECT status,owner_telegram_user_id,credential_ciphertext FROM telbot.bots WHERE tenant_id=%s AND id=%s FOR SHARE',(tenant,bid)).fetchone()
    if not current or current['status']!='active':return True
    owner=current['owner_telegram_user_id']
    owner_ok=db.execute("SELECT 1 AS ok FROM telbot.tenant_users WHERE tenant_id=%s AND telegram_user_id=%s AND role='owner' AND status='active'",(tenant,owner)).fetchone()
    if not owner_ok:return True
    paused=db.execute('SELECT status FROM telbot.chat_sessions WHERE tenant_id=%s AND bot_id=%s AND telegram_chat_id=%s',(tenant,bid,uid)).fetchone()
    if paused and paused['status']!='open':return True
    try:
        token=TokenVault(os.getenv('TELBOT_TOKEN_FERNET_KEY','')).decrypt(bytes(current['credential_ciphertext']))
        if token.split(':',1)[0]!=str(update['_bot_id']):return True
        db.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('showcase:'+str(bid)+':'+str(uid),))
        old=db.execute('SELECT state_ciphertext,last_update_id,updated_at FROM telbot.showcase_sessions WHERE tenant_id=%s AND bot_id=%s AND telegram_user_id=%s FOR UPDATE',(tenant,bid,uid)).fetchone()
        if old and old['last_update_id']>=update['update_id']:return True
        state=unseal(old['state_ciphertext']) if old and old['updated_at']>datetime.now(timezone.utc)-timedelta(hours=24) else {}
        reply=transition(state,text,actor.get('username'))
        outgoing=[]
        if reply.inquiry:
            recent=db.execute("SELECT count(*) AS n FROM telbot.showcase_inquiries WHERE tenant_id=%s AND bot_id=%s AND telegram_user_id=%s AND created_at>now()-interval '1 day'",(tenant,bid,uid)).fetchone()['n']
            if recent>=5:
                reply.text='امروز چند درخواست ثبت کرده‌ای؛ برای پیگیری از همان درخواست‌ها استفاده کن. درخواست تازه‌ای ذخیره نشد.'
                reply.state=state
            else:
                iid=uuid4(); payload={**reply.inquiry,'telegram_user_id':uid}
                db.execute('INSERT INTO telbot.showcase_inquiries(id,tenant_id,bot_id,telegram_user_id,source_update_id,industry,payload_ciphertext) VALUES (%s,%s,%s,%s,%s,%s,%s)',(iid,tenant,bid,uid,inbound_id,reply.inquiry['industry'],seal(payload)))
                code=str(iid)
                reply.text='✅ درخواستت ثبت شد\n\nکد پیگیری: '+code+'\n\nنیازت برای بررسی در صندوق درخواست‌های DirectPilot ذخیره شد. برای زمان و هزینه پس از بررسی هماهنگ می‌کنیم.'
                reply.state={}
                notification='📩 درخواست جدید ساخت ربات\n\nکد: '+code+'\nحوزه: '+BY_ID[payload['industry']].title+'\n\n'+payload['description']+'\n\nارتباط: '+payload['contact']+'\nشناسه تلگرام: '+str(uid)
                outgoing.append(('owner',{'chat_id':owner,'text':notification,'reply_markup':{'inline_keyboard':[[{'text':'گفت‌وگو با متقاضی','url':'tg://user?id='+str(uid)}]]}}))
        db.execute('INSERT INTO telbot.showcase_sessions(tenant_id,bot_id,telegram_user_id,state_ciphertext,last_update_id) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (bot_id,telegram_user_id) DO UPDATE SET state_ciphertext=EXCLUDED.state_ciphertext,last_update_id=EXCLUDED.last_update_id,updated_at=now()',(tenant,bid,uid,seal(reply.state),update['update_id']))
        outgoing.append(('customer',{'chat_id':uid,'text':reply.text,'reply_markup':keyboard(reply.rows)}))
        attempts=[]
        for kind,payload in outgoing:
            item=db.execute('INSERT INTO telbot.showcase_deliveries(tenant_id,bot_id,source_update_id,kind,payload_ciphertext) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (bot_id,source_update_id,kind) DO NOTHING RETURNING id',(tenant,bid,inbound_id,kind,seal(payload))).fetchone()
            if item:attempts.append((item['id'],payload))
        db.execute("UPDATE telbot.inbound_updates SET processing_status='processed',processed_at=now() WHERE id=%s AND tenant_id=%s AND bot_id=%s",(inbound_id,tenant,bid))
        db.commit()
    except (ShowcaseError,CredentialError):
        db.rollback();return True
    for attempt,payload in attempts:
        mid,error=await send_text(token,payload)
        status='sent' if mid else 'rejected' if error=='telegram_rejected' else 'unknown'
        db.execute('UPDATE telbot.showcase_deliveries SET status=%s WHERE id=%s AND tenant_id=%s AND bot_id=%s',(status,attempt,tenant,bid));db.commit()
    return True
