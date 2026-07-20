# AUDIT-01 — Test Baseline

**Environment:** existing repository `.venv`; no dependency installation/update and no test fixes.

## Execution results

| Command | Collected/result | Outcome |
|---|---|---|
| `.\.venv\Scripts\pytest.exe -q` | Collection stopped while importing `tests/conftest.py` | **Blocked:** `ModuleNotFoundError: No module named 'app'`; no tests ran. |
| `.\.venv\Scripts\python.exe -m pytest -q` | Collection stopped with four errors | **Blocked:** `PermissionError [WinError 5]` while scanning `test_temp_run/pytest`, `test_temp_run/pytest-full-comments`, `tools/pinggy-python/pinggy`, and its `.dist-info`. |
| `.\.venv\Scripts\python.exe -m pytest -q tests` | 82 collected; 82 passed; 0 failed; 0 skipped | **Passed** in 10.15 seconds; no warnings were printed. |

The third command is a scoped diagnostic of the repository's official `tests/` directory, not a repair of the two root-level collection blockers.

## Existing test inventory

| Path | Current coverage focus |
|---|---|
| `tests/test_health.py` | health/demo/catalog/chat/phone/order/operator/Finglish behavior |
| `tests/test_admin_console.py` | local admin boundary, origin checks, catalog draft/publish/alias/test isolation |
| `tests/test_content_studio.py` | media validation, content lifecycle, signed media, idempotent Instagram publish |
| `tests/test_instagram.py` | status/challenge/signature, DM dedupe, comment shapes/replies/module gates/failure claims |
| `tests/test_instagram_setup.py` | atomic local save, redaction, nonce/origin/expiry/input validation |
| `tests/test_telegram.py` | safe status, secret, webhook/dedupe/retry, command/text filters, local setup |
| `tests/test_manychat.py` | bearer/config, payload, dedupe/retry, duplicate-order protection |
| `tests/test_module_marketplace.py` | default modules, provider operations, dependencies/prices/slugs/tenant-host parsing |
| `tests/test_public_instagram_gateway.py` | reduced route exposure, legal pages, Meta verification/signature, safe logging |
| `tests/test_legal.py` | privacy and deletion pages |
| `tests/conftest.py` | creates tables and removes pytest-tagged connector/customer/conversation/order data around tests |

## Baseline interpretation

The existing test directory is green when explicitly targeted. A generic root invocation is not currently reproducible in this environment because of import-path behavior for the direct executable and unreadable non-test runtime/tool directories for module invocation.

**Needs Verification:** the canonical CI/test command and intended pytest discovery exclusions are not defined in `pytest.ini`, `pyproject.toml`, or a CI workflow in the reviewed scope.

