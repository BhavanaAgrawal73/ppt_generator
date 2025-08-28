import re

# 20 MB overall payload limit (adjust if needed)
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024

MASK = "••••••••"

_api_key_re = re.compile(r"([A-Za-z0-9_\-]{8,})")

def mask_api_key(s: str) -> str:
    if not s:
        return s
    if len(s) <= 8:
        return MASK
    return s[:4] + MASK + s[-2:]

def safe_len(s: str) -> int:
    return len(s or "")
