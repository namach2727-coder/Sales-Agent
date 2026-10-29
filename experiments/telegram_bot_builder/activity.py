"""Read-only, bounded delivery metadata for a tenant-authorized bot."""


def read_activity(db, tenant, bot_id):
    summary = db.execute("""SELECT incoming.received, outgoing.sent, outgoing.failed,
          outgoing.pending, now() AS checked_at
        FROM (SELECT count(*) AS received FROM telbot.inbound_updates
          WHERE tenant_id=%s AND bot_id=%s AND received_at>=now()-interval '24 hours') incoming
        CROSS JOIN (SELECT count(*) FILTER (WHERE delivery_status='sent') AS sent,
          count(*) FILTER (WHERE delivery_status='failed') AS failed,
          count(*) FILTER (WHERE delivery_status='queued') AS pending
          FROM telbot.outbound_messages WHERE tenant_id=%s AND bot_id=%s
            AND created_at>=now()-interval '24 hours') outgoing""", (tenant,bot_id,tenant,bot_id)).fetchone()
    events = db.execute("""SELECT i.received_at, i.processing_status,
          o.delivery_status, COALESCE(o.telegram_message_id IS NOT NULL,false) AS telegram_acknowledged
        FROM telbot.inbound_updates i
        LEFT JOIN LATERAL (SELECT delivery_status,telegram_message_id
          FROM telbot.outbound_messages WHERE tenant_id=i.tenant_id AND bot_id=i.bot_id
            AND source_update_id=i.id ORDER BY created_at DESC LIMIT 1) o ON true
        WHERE i.tenant_id=%s AND i.bot_id=%s AND i.received_at>=now()-interval '24 hours'
        ORDER BY i.received_at DESC,i.id DESC LIMIT 20""", (tenant,bot_id)).fetchall()
    return {'window_hours':24,'summary':dict(summary),'events':[dict(row) for row in events]}
