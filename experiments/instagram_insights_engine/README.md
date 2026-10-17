# DirectPilot Instagram Insights / AI — UAT development spike

**Not connected to Meta; not sold or delivered yet.** Independent feature branch `feature/uat-instagram-insights-engine-20261017`. Code is offline, no imported production app routes, no migrations, no encrypted account credentials used.

This build validates official-account metric snapshots, detects missing metrics, compares periods, prevents cross-account comparison and assembles an aggregate-only, evidence-first AI report request for later provider integration. **It does not send any request to Meta or an LLM** and does not generate an AI response. The separate UAT website shows a strictly labeled manual-data preview.

Proposed no-extra-charge 30-day AI report budgets: AUTOMATION=3, AI_ASSISTANT=15, only after real entitlement/backoffice feature gating, usage ledger and official Meta permission verification. Instagram paid-plan response limits remain unchanged. Do not charge users for a bonus until granted and tested.

**Integration gates:** Verify current official Instagram Login scopes/Insights availability per account. OAuth re-consent may be required; never infer permission from old messages. Read-only tenant+IG account scoped snapshots; handle user metrics vs media metrics, period compatibility, data suppression, Meta quota/errors. Store UTC reporting range, source and collection date. Introduce new schema with tenant/account FK + RLS/authorization + data deletion + time-bound retention. AI provider uses only aggregate authorized data with budgets, opt-in, no user DM text, and auditable report history. Test UAT then approve Production separately.

Run offline:
```bash
python -m unittest discover -s experiments/instagram_insights_engine -p 'test_*.py' -v
```
