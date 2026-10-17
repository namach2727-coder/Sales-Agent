-- UAT-only, rollback-only SQL assertion of manager webhook deduplication.
-- DB: telbot; branch: br-tiny-poetry-arz49v2o; no Production writes.
DO $smoke$
BEGIN
  BEGIN
    INSERT INTO telbot.manager_inbound_updates(telegram_update_id,event_type)
      VALUES (987654321,'managed_bot');
    BEGIN
      INSERT INTO telbot.manager_inbound_updates(telegram_update_id,event_type)
        VALUES (987654321,'managed_bot');
      RAISE EXCEPTION 'FAIL: manager update replay was accepted';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;
    RAISE EXCEPTION '__TELBOT_0002_TEST_ROLLBACK__';
  EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> '__TELBOT_0002_TEST_ROLLBACK__' THEN RAISE; END IF;
  END;
END $smoke$;
