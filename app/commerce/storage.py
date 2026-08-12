"""Private receipt storage boundary for the manual-payment MVP."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import uuid


class ReceiptValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class StoredReceipt:
    key: str
    content_type: str
    size: int
    sha256: str


class LocalPrivateReceiptStorage:
    ALLOWED = {
        "image/jpeg": lambda value: value.startswith(b"\xff\xd8\xff"),
        "image/png": lambda value: value.startswith(b"\x89PNG\r\n\x1a\n"),
        "application/pdf": lambda value: value.startswith(b"%PDF-"),
    }

    def __init__(self, root: str, *, max_bytes: int) -> None:
        self.root = Path(root).resolve()
        self.max_bytes = max_bytes

    def store(self, *, tenant_public_id: str, payment_public_id: str, content_type: str, data: bytes) -> StoredReceipt:
        normalized = content_type.partition(";")[0].strip().casefold()
        validator = self.ALLOWED.get(normalized)
        if validator is None or not validator(data):
            raise ReceiptValidationError("unsupported or invalid receipt content")
        if not data or len(data) > self.max_bytes:
            raise ReceiptValidationError("receipt size is invalid")
        suffix = {"image/jpeg": ".jpg", "image/png": ".png", "application/pdf": ".pdf"}[normalized]
        key = f"{tenant_public_id}/{payment_public_id}/{uuid.uuid4().hex}{suffix}"
        target = (self.root / key).resolve()
        if self.root not in target.parents:
            raise ReceiptValidationError("invalid storage key")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        try:
            with temporary.open("xb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return StoredReceipt(key, normalized, len(data), hashlib.sha256(data).hexdigest())

    def delete(self, key: str) -> None:
        target = (self.root / key).resolve()
        if self.root in target.parents:
            target.unlink(missing_ok=True)
