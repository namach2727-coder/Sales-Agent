# AUDIT-01 — Media and Voice Discovery

## Search result classification

Repository-wide searches covered `audio`, `voice`, `attachment`, `attachments`, `media`, `mime`, `transcript`, `speech`, `whisper`, and `download` across source, tests, scripts, README, dependency, and environment-example files.

| Path and symbol | Match and current behavior |
|---|---|
| `app/telegram.py::extract_incoming_messages()` | Explicitly ignores media and accepts only private messages with non-empty `message.text`. |
| `app/instagram.py::extract_incoming_messages()` | Requires `message.text`; attachment-only message events do not produce `IncomingInstagramMessage`. |
| `app/instagram.py::extract_incoming_comments()` | Reads Meta comment `media.id` and `media_product_type` as post metadata; it does not download that media. |
| `app/manychat.py::ManyChatContact` | Accepts `last_input_text`; no attachment/audio field exists in the request schema. |
| `app/media_storage.py::decode_manager_jpeg()/save_product_image()` | Decodes a manager-supplied JPEG data URL, verifies structure/size/pixels, hashes it, and stores it under `MEDIA_STORAGE_ROOT`. |
| `app/static/admin_content.js::prepareContentImage()` | Reads a manager-selected image in the browser, fits it onto a 1080×1080 canvas, converts it to JPEG, then uploads a data URL. |
| `app/models.py::ProductMediaAsset` | Stores JPEG metadata and a server-generated storage key; binary bytes remain on local disk. |
| `app/public_media.py::public_product_image()` | Serves a ready local JPEG only with a valid expiring HMAC URL. |
| `app/instagram_publishing.py::InstagramContentPublisher.publish_image()` | Sends the signed image URL to Meta for single-image publishing; Meta fetches the URL. |
| `app/models.py::InstagramMediaProduct` | Stores Meta post-media ID to product mapping, not media bytes. |
| `tests/test_content_studio.py` | Tests upload validation/private preview, signed URL tampering, publishing idempotency, and media mapping. |
| `tests/test_instagram.py` | Tests comment media IDs/mappings; not inbound media download. |

## Current classification

- **Inbound attachments:** absent. Instagram and Telegram parsers are text-only; ManyChat input is text-only.
- **Voice/audio:** absent. No audio/voice model, MIME policy, downloader, transcription, speech/Whisper integration, dependency, route, or test was found.
- **Media handling:** implemented only for manager-uploaded product images and Instagram post identifiers/publishing.
- **Download behavior:** no inbound connector media downloader was found. The server writes uploaded JPEG bytes locally; the public media route serves them, and Meta is expected to fetch a signed URL during publishing.
- **Ignored media:** Telegram documents media as ignored. Instagram attachment-only messages are filtered by the required text checks rather than persisted as unsupported events.

## Needs Verification

1. **Needs Verification:** whether production Meta payloads containing both text and attachments should retain attachment metadata is not stated; current code keeps text only.
2. **Needs Verification:** `app/static/privacy.html` mentions “submitted media,” but current connector implementations do not accept inbound customer media; intended legal/product scope should be confirmed separately.

