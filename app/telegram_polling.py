import argparse
import asyncio

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.telegram import (
    TelegramAPIError,
    TelegramClient,
    is_configured,
    process_telegram_payload,
)


async def run_polling(once: bool = False) -> None:
    settings = get_settings()
    if not is_configured(settings.telegram_bot_token):
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured in .env")
    if not settings.telegram_polling_enabled:
        raise RuntimeError("TELEGRAM_POLLING_ENABLED must be true in .env")
    if not settings.telegram_send_enabled:
        raise RuntimeError("TELEGRAM_SEND_ENABLED must be true before polling")

    Base.metadata.create_all(bind=engine)
    client = TelegramClient(settings)
    webhook_info = await client.get_webhook_info()
    if webhook_info.get("url"):
        raise RuntimeError(
            "A Telegram webhook is active. Remove it before starting local polling."
        )

    offset: int | None = None
    print("Telegram polling started. Press Ctrl+C to stop.")
    while True:
        updates = await client.get_updates(offset=offset)
        for update in updates:
            update_id = update.get("update_id")
            if not isinstance(update_id, int):
                continue
            with SessionLocal() as db:
                result = await process_telegram_payload(update, db, client, settings)
            if result["failed"]:
                print(f"Update {update_id} failed and will be retried.")
                break
            offset = update_id + 1
        if once:
            return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Telegram bot with local polling")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Fetch one batch and exit (useful for diagnostics)",
    )
    args = parser.parse_args()
    try:
        asyncio.run(run_polling(once=args.once))
    except (RuntimeError, TelegramAPIError) as exc:
        print(f"Telegram polling stopped: {exc}")
        raise SystemExit(1) from None
    except KeyboardInterrupt:
        print("Telegram polling stopped.")


if __name__ == "__main__":
    main()
