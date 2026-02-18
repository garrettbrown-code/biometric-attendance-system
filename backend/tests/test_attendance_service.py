from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.db.repository import SessionRow
from app.services.attendance_service import add_attendance


def _today_str() -> str:
    return datetime.now().date().strftime("%Y-%m-%d")


@patch("app.services.attendance_service.repository.get_class_by_code")
def test_add_attendance_class_missing(mock_get_class_by_code, tmp_path: Path) -> None:
    mock_get_class_by_code.return_value = None

    result = add_attendance(
        db=MagicMock(),
        code="csce_4900_500",
        euid="gdb2356",
        student_location=(33.0, -97.0),
        submitted_photo_b64="abc",
        user_data_dir=tmp_path,
    )
    assert result.status == "error"
    assert result.error == "Class does not exist"


@patch("app.services.attendance_service.repository.get_session_for_date")
@patch("app.services.attendance_service.repository.get_class_by_code")
def test_add_attendance_no_class_today(mock_get_class_by_code, mock_get_session, tmp_path: Path) -> None:
    mock_get_class_by_code.return_value = {"lat": 33.0, "lon": -97.0}
    mock_get_session.return_value = None

    result = add_attendance(
        db=MagicMock(),
        code="csce_4900_500",
        euid="gdb2356",
        student_location=(33.0, -97.0),
        submitted_photo_b64="abc",
        user_data_dir=tmp_path,
    )
    assert result.status == "error"
    assert result.error == "No class on date"


@patch("app.services.attendance_service.verify_face_match")
@patch("app.services.attendance_service.distance_feet")
@patch("app.services.attendance_service.repository.upsert_attendance")
@patch("app.services.attendance_service.repository.get_session_for_date")
@patch("app.services.attendance_service.repository.get_class_by_code")
def test_add_attendance_success(
    mock_get_class_by_code,
    mock_get_session,
    mock_upsert,
    mock_distance,
    mock_face,
    tmp_path: Path,
) -> None:
    mock_get_class_by_code.return_value = {"lat": 33.0, "lon": -97.0}

    # Put session time at "now" so it's within time window
    now = datetime.now()
    mock_get_session.return_value = SessionRow(
        id=123,
        code="csce_4900_500",
        session_date=_today_str(),
        session_time=now.strftime("%H:%M:%S"),
    )

    mock_distance.return_value = 10.0  # within 30 feet
    mock_face.return_value = type("R", (), {"status": "success", "error": None})()

    result = add_attendance(
        db=MagicMock(),
        code="csce_4900_500",
        euid="gdb2356",
        student_location=(33.0, -97.0),
        submitted_photo_b64="abc",
        user_data_dir=tmp_path,
    )
    assert result.status == "success"
    mock_upsert.assert_called_once()


@patch("app.services.attendance_service.repository.get_session_for_date")
@patch("app.services.attendance_service.repository.get_class_by_code")
def test_add_attendance_outside_time_window(mock_get_class_by_code, mock_get_session, tmp_path: Path) -> None:
    mock_get_class_by_code.return_value = {"lat": 33.0, "lon": -97.0}

    # Session time far in the past (over 30 min)
    mock_get_session.return_value = SessionRow(
        id=1,
        code="csce_4900_500",
        session_date=_today_str(),
        session_time="00:00:00",
    )

    result = add_attendance(
        db=MagicMock(),
        code="csce_4900_500",
        euid="gdb2356",
        student_location=(33.0, -97.0),
        submitted_photo_b64="abc",
        user_data_dir=tmp_path,
        time_window_minutes=1,  # ensure it fails regardless of current time
    )
    assert result.status == "error"
    assert result.error == "Outside time range"


@patch("app.services.attendance_service.verify_face_match")
@patch("app.services.attendance_service.distance_feet")
@patch("app.services.attendance_service.repository.get_session_for_date")
@patch("app.services.attendance_service.repository.get_class_by_code")
def test_add_attendance_too_far(
    mock_get_class_by_code,
    mock_get_session,
    mock_distance,
    mock_face,
    tmp_path: Path,
) -> None:
    mock_get_class_by_code.return_value = {"lat": 33.0, "lon": -97.0}

    now = datetime.now()
    mock_get_session.return_value = SessionRow(
        id=1,
        code="csce_4900_500",
        session_date=_today_str(),
        session_time=now.strftime("%H:%M:%S"),
    )

    mock_distance.return_value = 500.0  # too far

    result = add_attendance(
        db=MagicMock(),
        code="csce_4900_500",
        euid="gdb2356",
        student_location=(33.0, -97.0),
        submitted_photo_b64="abc",
        user_data_dir=tmp_path,
        max_distance_feet=30.0,
    )
    assert result.status == "error"
    assert result.error == "Too far from class"
    mock_face.assert_not_called()
