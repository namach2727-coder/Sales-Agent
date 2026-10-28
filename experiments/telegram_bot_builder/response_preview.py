"""Pure rule selection for the builder: no storage, vault or network effects."""
from typing import Any

try:
    from .builder_models import PreviewInput
    from .core import is_start_command, keyword_matches
except ImportError:
    from builder_models import PreviewInput
    from core import is_start_command, keyword_matches


def preview_response(snapshot: PreviewInput) -> dict[str, Any]:
    if is_start_command(snapshot.text):
        return {'action': 'greeting', 'response_text': snapshot.greeting, 'executed': False}
    for index, rule in enumerate(snapshot.rules, start=1):
        if not rule.enabled or not keyword_matches(rule.keyword, rule.match_mode, snapshot.text):
            continue
        if rule.action_type == 'api':
            # Never present configured fallback as a successful provider response.
            return {'action': 'api', 'rule_index': index,
                    'fallback_text': rule.response_text, 'executed': False}
        return {'action': 'text', 'rule_index': index,
                'response_text': rule.response_text, 'executed': False}
    return {'action': 'fallback', 'response_text': snapshot.fallback_reply, 'executed': False}
