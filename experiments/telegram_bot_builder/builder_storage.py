"""Tenant-scoped configuration snapshots, including encrypted API actions."""
import os
from fastapi import HTTPException
try:
    from .api_actions import ApiActionError, materialize_call, seal_call, open_call, public_call
except ImportError:
    from api_actions import ApiActionError, materialize_call, seal_call, open_call, public_call


def api_schema_ready(db):
    row = db.execute("SELECT version FROM telbot.schema_migrations WHERE version='0003_rule_api_calls'", ()).fetchone()
    return bool(row and row['version'] == '0003_rule_api_calls')


def read_rules(db, tenant, config_id, *, public=False, ready=None):
    ready = api_schema_ready(db) if ready is None else ready
    extra = ',action_type,api_request_ciphertext' if ready else ''
    rows = db.execute(f"""SELECT id,keyword,match_mode,response_text,priority,enabled{extra}
        FROM telbot.reply_rules WHERE tenant_id=%s AND configuration_id=%s
        ORDER BY priority ASC LIMIT 100""", (tenant, config_id)).fetchall()
    rules = []
    for source in rows:
        row = dict(source)
        row['action_type'] = row.get('action_type', 'text')
        if public:
            encrypted = row.pop('api_request_ciphertext', None)
            row['api'] = None
            if encrypted:
                try:
                    row['api'] = public_call(open_call(encrypted, os.getenv('TELBOT_TOKEN_FERNET_KEY', '')))
                except ApiActionError:
                    # Refuse editing an unreadable API version; never silently convert to text.
                    raise HTTPException(status_code=503, detail='API configuration unavailable') from None
        rules.append(row)
    return rules


def add_snapshot_rules(db, tenant, bot_id, new_id, previous, body):
    ready = api_schema_ready(db)
    if body.rules is None:
        if previous:
            columns = ',action_type,api_request_ciphertext' if ready else ''
            db.execute(f"""INSERT INTO telbot.reply_rules
                (tenant_id,configuration_id,keyword,match_mode,response_text,priority,enabled{columns})
                SELECT tenant_id,%s,keyword,match_mode,response_text,priority,enabled{columns}
                FROM telbot.reply_rules WHERE tenant_id=%s AND configuration_id=%s""",
                (new_id, tenant, previous['id']))
    else:
        for priority, rule in enumerate(body.rules):
            ciphertext = None
            if rule.action_type == 'api':
                if not ready:
                    raise HTTPException(status_code=503, detail='API actions schema not ready')
                previous_call = None
                if rule.source_rule_id and previous:
                    source = db.execute("""SELECT r.api_request_ciphertext FROM telbot.reply_rules r
                        JOIN telbot.configuration_versions c ON c.id=r.configuration_id AND c.tenant_id=r.tenant_id
                        WHERE r.id=%s AND r.tenant_id=%s AND c.bot_id=%s AND c.id=%s AND r.action_type='api'""",
                        (rule.source_rule_id, tenant, bot_id, previous['id'])).fetchone()
                    if not source:
                        raise HTTPException(status_code=409, detail='API source rule changed')
                    try:
                        previous_call = open_call(source['api_request_ciphertext'], os.getenv('TELBOT_TOKEN_FERNET_KEY', ''))
                    except ApiActionError:
                        raise HTTPException(status_code=503, detail='API configuration unavailable') from None
                try:
                    ciphertext = seal_call(materialize_call(rule.api, previous_call), os.getenv('TELBOT_TOKEN_FERNET_KEY', ''))
                except ApiActionError as exc:
                    status = 422 if str(exc) == 'api_credential_required' else 503
                    raise HTTPException(status_code=status, detail=str(exc)) from None
            args = (tenant, new_id, rule.keyword, rule.match_mode, rule.response_text, priority, rule.enabled)
            if ready:
                db.execute("""INSERT INTO telbot.reply_rules(tenant_id,configuration_id,keyword,match_mode,
                    response_text,priority,enabled,action_type,api_request_ciphertext)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""", (*args, rule.action_type, ciphertext))
            else:
                db.execute("""INSERT INTO telbot.reply_rules(tenant_id,configuration_id,keyword,match_mode,
                    response_text,priority,enabled) VALUES (%s,%s,%s,%s,%s,%s,%s)""", args)
    if previous:
        # Other builder surfaces are not editable here. Preserve their existing content.
        db.execute("""INSERT INTO telbot.menu_buttons(tenant_id,configuration_id,label,action_type,action_value,sort_order)
            SELECT tenant_id,%s,label,action_type,action_value,sort_order FROM telbot.menu_buttons
            WHERE tenant_id=%s AND configuration_id=%s""", (new_id, tenant, previous['id']))
        db.execute("""INSERT INTO telbot.faq_entries(tenant_id,configuration_id,question,answer,sort_order)
            SELECT tenant_id,%s,question,answer,sort_order FROM telbot.faq_entries
            WHERE tenant_id=%s AND configuration_id=%s""", (new_id, tenant, previous['id']))
