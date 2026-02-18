from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.db import repository
from app.services.face_service import verify_face_match
from app.services.geo_service import distance_feet


DEFAULT_MAX_DISTANCE_FEET = 30.0
DEFAULT_TIME_WINDOW_MINUTES = 30


@dataclass(frozen=True)
class AttendanceResult:
    status: str  # "success" | "error"
    error: Optional[str] = None


def add_attendance(
    *,
    db,
    code: str,
    euid: str,
    student_location: tuple[float, float],
    submitted_photo_b64: str,
    user_data_dir: Path,
    max_distance_feet: float = DEFAULT_MAX_DISTANCE_FEET,
    time_window_minutes: int = DEFAULT_TIME_WINDOW_MINUTES,
    face_tolerance: float = 0.6,
) -> AttendanceResult:
    # 1) Class exists + get location
    class_info = repository.get_class_by_code(db, code=code)
    if class_info is None:
        return AttendanceResult(status="error", error="Class does not exist")

    # 2) Session exists today
    today = datetime.now().date().strftime("%Y-%m-%d")
    session = repository.get_session_for_date(db, code=code, on_date=today)
    if session is None:
        return AttendanceResult(status="error", error="No class on date")

    # 3) Time window check
    session_dt = datetime.strptime(
        f"{session.session_date} {session.session_time}",
        "%Y-%m-%d %H:%M:%S",
    )
    now = datetime.now()
    diff_seconds = abs((now - session_dt).total_seconds())
    if diff_seconds > time_window_minutes * 60:
        return AttendanceResult(status="error", error="Outside time range")

    # 4) Distance check
    class_location = (float(class_info["lat"]), float(class_info["lon"]))
    dist = distance_feet(student_location, class_location)
    if dist > max_distance_feet:
        return AttendanceResult(status="error", error="Too far from class")

    # 5) Face match check
    reference_path = user_data_dir / "Student" / euid / "reference_image.jpg"
    face_result = verify_face_match(
        submitted_photo_b64=submitted_photo_b64,
        reference_image_path=reference_path,
        tolerance=face_tolerance,
    )
    if face_result.status != "success":
        return AttendanceResult(status="error", error=face_result.error or "Face verification failed")

    # 6) Persist
    repository.upsert_attendance(db, session_id=session.id, student_euid=euid, attended=1)
    return AttendanceResult(status="success")
