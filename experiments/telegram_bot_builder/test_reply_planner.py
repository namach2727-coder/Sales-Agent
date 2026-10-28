import pytest
from .core import BotConfiguration, ReplyRule
from .reply_planner import plan_private_reply


def configuration():
    return BotConfiguration('tenant-a', 42, 'Welcome', 'Fallback', (ReplyRule('قیمت', 'Price'),))


def update(text='/start'):
    return {'update_id': 1, 'message': {'from': {'id': 123, 'is_bot': False}, 'chat': {'id': 123, 'type': 'private'}, 'text': text}}


@pytest.mark.parametrize('text,expected', [('/start', 'Welcome'), ('/start campaign', 'Welcome'), ('قیمت', 'Price'), ('unknown', 'Fallback')])
def test_reply_selection(text, expected):
    assert plan_private_reply(configuration(), update(text), tenant_id='tenant-a', bot_id=42) == {'chat_id': 123, 'text': expected}


@pytest.mark.parametrize('tenant,bot', [('tenant-b', 42), ('tenant-a', 43)])
def test_cross_scope_rejected(tenant, bot):
    with pytest.raises(ValueError):
        plan_private_reply(configuration(), update(), tenant_id=tenant, bot_id=bot)


@pytest.mark.parametrize('case', ['bot', 'group', 'foreign_sender', 'no_text', 'edited'])
def test_ignored_messages(case):
    event = update()
    if case == 'bot': event['message']['from']['is_bot'] = True
    if case == 'group': event['message']['chat']['type'] = 'group'
    if case == 'foreign_sender': event['message']['from']['id'] = 456
    if case == 'no_text': event['message'].pop('text')
    if case == 'edited': event['edited_message'] = event.pop('message')
    assert plan_private_reply(configuration(), event, tenant_id='tenant-a', bot_id=42) is None
