import re


def normalize_phone(raw: str) -> str:
    cleaned = re.sub(r"[^\d+]", "", raw)
    if cleaned.startswith("+91"):
        return "91" + cleaned[3:]
    if cleaned.startswith("91") and len(cleaned) == 12:
        return cleaned
    if len(cleaned) == 10:
        return "91" + cleaned
    return cleaned
