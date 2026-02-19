from __future__ import annotations

import base64

import pytest
from pydantic import ValidationError

from app.models.requests import AddAttendanceRequest, AddClassRequest


def test_valid_add_class_request_passes() -> None:
    payload = {
        "code": "csce_4900_500",
        "euid": "gdb2356",
        "location": [33.214, -97.133],
        "start_date": "2025-04-01",
        "end_date": "2025-04-15",
        "times": {"Monday": "09:00:00", "Wednesday": "09:00:00"},
    }
    req = AddClassRequest.model_validate(payload)
    assert req.code == "csce_4900_500"
    assert req.euid == "gdb2356"
    assert req.location == (33.214, -97.133)


@pytest.mark.parametrize(
    "bad_code",
    [
        "CSCE_4900_500",  # uppercase
        "csce4900_500",  # missing underscore
        "csce_490_500",  # wrong digits
        "csc_4900_500",  # wrong letters count
        "csce_4900_50",  # wrong last digits count
    ],
)
def test_class_code_format_rejected(bad_code: str) -> None:
    payload = {
        "code": bad_code,
        "euid": "gdb2356",
        "location": [33.214, -97.133],
        "start_date": "2025-04-01",
        "end_date": "2025-04-15",
        "times": {"Monday": "09:00:00"},
    }
    with pytest.raises(ValidationError):
        AddClassRequest.model_validate(payload)


@pytest.mark.parametrize(
    "bad_euid",
    [
        "gdb235",  # too short
        "gdb23567",  # too long
        "gd2356",  # only 2 letters
        "GDB2356",  # uppercase
        "gdb23a6",  # letter in digits
    ],
)
def test_euid_format_rejected(bad_euid: str) -> None:
    payload = {
        "code": "csce_4900_500",
        "euid": bad_euid,
        "location": [33.214, -97.133],
        "start_date": "2025-04-01",
        "end_date": "2025-04-15",
        "times": {"Monday": "09:00:00"},
    }
    with pytest.raises(ValidationError):
        AddClassRequest.model_validate(payload)


def test_location_bounds_rejected() -> None:
    payload = {
        "code": "csce_4900_500",
        "euid": "gdb2356",
        "location": [120.0, -97.133],  # invalid latitude
        "start_date": "2025-04-01",
        "end_date": "2025-04-15",
        "times": {"Monday": "09:00:00"},
    }
    with pytest.raises(ValidationError):
        AddClassRequest.model_validate(payload)


def test_time_format_rejected() -> None:
    payload = {
        "code": "csce_4900_500",
        "euid": "gdb2356",
        "location": [33.214, -97.133],
        "start_date": "2025-04-01",
        "end_date": "2025-04-15",
        "times": {"Monday": "9:00:00"},  # should be 09:00:00
    }
    with pytest.raises(ValidationError):
        AddClassRequest.model_validate(payload)


def test_valid_add_attendance_request_passes() -> None:
    fake_jpg_bytes = b"\xff\xd8\xff\xe0" + b"fakejpg"  # doesn't need to be real yet
    payload = {
        "code": "csce_4900_500",
        "euid": "gdb2356",
        "location": [33.214, -97.133],
        "photo": base64.b64encode(fake_jpg_bytes).decode("utf-8"),
    }
    req = AddAttendanceRequest.model_validate(payload)
    assert req.code == "csce_4900_500"
    assert req.euid == "gdb2356"
