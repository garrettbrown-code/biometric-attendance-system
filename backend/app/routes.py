from __future__ import annotations

from flask import Blueprint, jsonify, request, current_app
from pydantic import ValidationError

from app.db.connection import get_db
from app.models.requests import (
    AddAttendanceRequest,
    AddClassRequest,
    GetStudentAttendanceRequest,
    GetClassAttendanceRequest,
    GetClassScheduleRequest,
    GetProfessorScheduleRequest,
    GetProfessorClassCodesRequest,
)

from app.db import repository
from app.services.attendance_service import add_attendance

from app.config import Config

bp = Blueprint("api", __name__)


def _cfg() -> Config:
    return current_app.config["APP_CONFIG"]


def _validation_error(e: ValidationError):
    return jsonify(
        {
            "status": "error",
            "error": "Validation error",
            "details": e.errors(),
        }
    ), 400


@bp.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@bp.post("/classes")
def post_class():
    try:
        payload = AddClassRequest.model_validate(request.get_json())
    except ValidationError as e:
        return _validation_error(e)

    cfg = _cfg()
    db = get_db()

    try:
        created = repository.add_class(
            db,
            code=payload.code,
            professor_euid=payload.euid,
            lat=payload.location[0],
            lon=payload.location[1],
            start_date=payload.start_date,
            end_date=payload.end_date,
            times=payload.times,
        )
    except ValueError as e:
        # class already exists, etc.
        return jsonify({"status": "error", "error": str(e)}), 409
    except Exception as e:
        return jsonify({"status": "error", "error": "Server error"}), 500

    return jsonify({"status": "success", "sessions_created": created}), 201


@bp.post("/attendance")
def post_attendance():
    try:
        payload = AddAttendanceRequest.model_validate(request.get_json())
    except ValidationError as e:
        return _validation_error(e)

    cfg = _cfg()
    db = get_db()

    result = add_attendance(
        db=db,
        code=payload.code,
        euid=payload.euid,
        student_location=payload.location,
        submitted_photo_b64=payload.photo,
        user_data_dir=cfg.user_data_dir,
        max_distance_feet=float(cfg.max_distance_feet),
        time_window_minutes=int(cfg.time_window_minutes),
    )

    status_code = 200 if result.status == "success" else 400
    return jsonify({"status": result.status, "error": result.error}), status_code


@bp.get("/students/<euid>/attendance")
def get_student_attendance(euid: str):
    # Validate the path param using your Pydantic model
    try:
        payload = GetStudentAttendanceRequest.model_validate({"euid": euid})
    except ValidationError as e:
        return _validation_error(e)

    db = get_db()
    rows = repository.get_student_attendance(db, student_euid=payload.euid)
    return jsonify({"status": "success", "attendance": rows}), 200


@bp.get("/classes/<code>/attendance")
def get_class_attendance(code: str):
    try:
        payload = GetClassAttendanceRequest.model_validate({"code": code})
    except ValidationError as e:
        return _validation_error(e)

    db = get_db()
    rows = repository.get_class_attendance(db, code=payload.code)
    return jsonify({"status": "success", "attendance": rows}), 200


@bp.get("/classes/<code>/schedule")
def get_class_schedule(code: str):
    try:
        payload = GetClassScheduleRequest.model_validate({"code": code})
    except ValidationError as e:
        return _validation_error(e)

    db = get_db()
    rows = repository.get_class_schedule(db, code=payload.code)
    return jsonify({"status": "success", "days": rows}), 200


@bp.get("/professors/<euid>/schedule")
def get_professor_schedule(euid: str):
    try:
        payload = GetProfessorScheduleRequest.model_validate({"euid": euid})
    except ValidationError as e:
        return _validation_error(e)

    db = get_db()
    rows = repository.get_professor_schedule(db, professor_euid=payload.euid)
    return jsonify({"status": "success", "classes": rows}), 200


@bp.get("/professors/<euid>/classes")
def get_professor_class_codes(euid: str):
    try:
        payload = GetProfessorClassCodesRequest.model_validate({"euid": euid})
    except ValidationError as e:
        return _validation_error(e)

    db = get_db()
    codes = repository.get_professor_class_codes(db, professor_euid=payload.euid)
    return jsonify({"status": "success", "codes": codes}), 200
