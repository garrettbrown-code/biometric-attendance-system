from __future__ import annotations

import base64
import re
from typing import Any

# Strict formats (lowercase only)
EUID_RE = re.compile(r"^[a-z]{3}\d{4}$")  # gdb2356
CLASS_CODE_RE = re.compile(r"^[a-z]{4}_\d{4}_\d{3}$")  # csce_4900_500
JOIN_CODE_RE = re.compile(r"^[A-Z0-9]{6,12}$")  # e.g. 8 chars, uppercase letters+digits

WEEKDAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}


def validate_euid(euid: str) -> str:
    euid = euid.strip()
    if euid != euid.lower():
        raise ValueError("euid must be lowercase")
    if not EUID_RE.fullmatch(euid):
        raise ValueError("euid must match 'abc1234' (3 letters + 4 digits, lowercase)")
    return euid


def validate_class_code(code: str) -> str:
    code = code.strip()
    if code != code.lower():
        raise ValueError("code must be lowercase")
    if not CLASS_CODE_RE.fullmatch(code):
        raise ValueError("code must match 'abcd_1234_123' (4 letters_4 digits_3 digits, lowercase)")
    return code


def validate_location(location: Any) -> tuple[float, float]:
    if not isinstance(location, (list, tuple)) or len(location) != 2:
        raise ValueError("location must be a 2-item list/tuple: [lat, lon]")
    lat = float(location[0])
    lon = float(location[1])
    if not (-90.0 <= lat <= 90.0):
        raise ValueError("latitude must be between -90 and 90")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError("longitude must be between -180 and 180")
    return (lat, lon)


def validate_time_hhmmss(t: str) -> str:
    t = t.strip()
    if not re.fullmatch(r"\d{2}:\d{2}:\d{2}", t):
        raise ValueError("time must be in HH:MM:SS format")
    hh, mm, ss = map(int, t.split(":"))
    if not (0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 59):
        raise ValueError("time must be a valid 24-hour time")
    return t


def validate_date_yyyymmdd(d: str) -> str:
    d = d.strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
        raise ValueError("date must be in YYYY-MM-DD format")
    return d


def validate_base64_image(b64: str, *, max_bytes: int = 4_000_000) -> str:
    if not isinstance(b64, str) or not b64.strip():
        raise ValueError("photo must be a base64-encoded string")
    b64 = b64.strip()

    try:
        decoded = base64.b64decode(b64, validate=True)
    except Exception as e:
        raise ValueError("photo must be valid base64") from e

    if len(decoded) > max_bytes:
        raise ValueError(f"photo is too large (> {max_bytes} bytes)")

    return b64


def validate_join_code(code: str) -> str:
    code = code.strip()
    if code != code.upper():
        raise ValueError("join_code must be uppercase")
    if not JOIN_CODE_RE.fullmatch(code):
        raise ValueError("join_code must be 6-12 chars (A-Z, 0-9)")
    return code