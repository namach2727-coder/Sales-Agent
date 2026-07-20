import re
import unicodedata


PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def normalize_catalog_text(value: str) -> str:
    """Create the stable, shared form used when publishing and matching aliases."""
    normalized = (
        unicodedata.normalize("NFKC", value)
        .translate(PERSIAN_DIGITS)
        .translate(ARABIC_DIGITS)
        .replace("ي", "ی")
        .replace("ك", "ک")
        .replace("‌", " ")
        .lower()
        .strip()
    )
    normalized = "".join(
        " " if unicodedata.category(character)[0] in {"P", "S"} else character
        for character in normalized
    )
    return re.sub(r"\s+", " ", normalized).strip()


def phrase_is_present(message: str, phrase: str) -> bool:
    normalized_message = normalize_catalog_text(message)
    normalized_phrase = normalize_catalog_text(phrase)
    if not normalized_phrase:
        return False
    pattern = rf"(?<!\w){re.escape(normalized_phrase)}(?!\w)"
    return re.search(pattern, normalized_message, flags=re.UNICODE) is not None

