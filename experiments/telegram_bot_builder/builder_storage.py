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
    rows = db.execute(f"""SELECT id,keyword,match_mode,response_text,priority,enabled{extra},
        EXISTS (SELECT 1 FROM telbot.menu_buttons m WHERE m.tenant_id=r.tenant_id
          AND m.configuration_id=r.configuration_id AND m.action_type='reply'
          AND m.label=r.keyword AND m.action_value=r.keyword) AS show_button
        FROM telbot.reply_rules r WHERE r.tenant_id=%s AND r.configuration_id=%s
        ORDER BY priority ASC LIMIT 100""", (tenant, config_id)).fetchall()
    rules = []
    for source in rows:
        row = dict(source)
        row['action_type'] = row.get('action_type', 'text')
        row['show_button'] = bool(row.get('show_button', False))
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
    # Older clients omit show_button and retain the entire legacy menu unchanged.
    edit_buttons = body.rules is not None and (body.replace_reply_buttons or any(r.show_button is not None for r in body.rules))
    buttons = [r for r in (body.rules or []) if r.show_button] if edit_buttons else []
    if len(buttons) > 12:
        raise HTTPException(status_code=422, detail='At most 12 menu buttons')
    for index, rule in enumerate(buttons):
        db.execute("""INSERT INTO telbot.menu_buttons(tenant_id,configuration_id,label,action_type,action_value,sort_order)
            VALUES (%s,%s,%s,'reply',%s,%s)""", (tenant,new_id,rule.keyword,rule.keyword,index))
    if previous:
        if edit_buttons:
            # Only keyword-backed reply buttons belong to this surface. Preserve all other menus.
            db.execute("""INSERT INTO telbot.menu_buttons(tenant_id,configuration_id,label,action_type,action_value,sort_order)
                SELECT tenant_id,%s,label,action_type,action_value,
                  %s + row_number() OVER (ORDER BY sort_order) - 1
                FROM telbot.menu_buttons WHERE tenant_id=%s AND configuration_id=%s
                  AND NOT (action_type='reply' AND label=action_value AND EXISTS (
                    SELECT 1 FROM telbot.reply_rules r WHERE r.tenant_id=telbot.menu_buttons.tenant_id
                      AND r.configuration_id IN (%s,%s)
                      AND r.keyword=telbot.menu_buttons.action_value))""",
                (new_id,len(buttons),tenant,previous['id'],previous['id'],new_id))
        else:
            db.execute("""INSERT INTO telbot.menu_buttons(tenant_id,configuration_id,label,action_type,action_value,sort_order)
                SELECT tenant_id,%s,label,action_type,action_value,sort_order FROM telbot.menu_buttons
                WHERE tenant_id=%s AND configuration_id=%s""", (new_id,tenant,previous['id']))
        db.execute("""INSERT INTO telbot.faq_entries(tenant_id,configuration_id,question,answer,sort_order)
            SELECT tenant_id,%s,question,answer,sort_order FROM telbot.faq_entries
            WHERE tenant_id=%s AND configuration_id=%s""", (new_id,tenant,previous['id']))
