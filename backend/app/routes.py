from __future__ import annotations

import logging
import uuid

from flask import Blueprint, current_app, g, jsonify, request
from pydantic import ValidationError

from app.config import Config
from app.db import repository
from app.db.connection import get_db
from app.models.requests import (
    AddAttendanceRequest,
    AddClassRequest,
    GetClassAttendanceRequest,
    GetClassScheduleRequest,
    GetProfessorClassCodesRequest,
    GetProfessorScheduleRequest,
    GetStudentAttendanceRequest,
)
from app.services.attendance_service import add_attendance

bp = Blueprint("api", __name__)
logger = logging.getLogger(__name__)


def _cfg() -> Config:
    return current_app.config["APP_CONFIG"]


def _request_id() -> str:
    return getattr(g, "request_id", "")


def _validation_error(e: ValidationError):
    return (
        jsonify(
            {
                "status": "error",
                "error": "Validation error",
                "details": e.errors(),
                "request_id": _request_id(),
            }
        ),
        400,
    )


def _error(status_code: int, message: str):
    return (
        jsonify({"status": "error", "error": message, "request_id": _request_id()}),
        status_code,
    )


@bp.before_app_request
def attach_request_id():
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    g.request_id = rid


@bp.after_app_request
def add_request_id_header(response):
    response.headers["X-Request-ID"] = _request_id()
    return response


@bp.app_errorhandler(Exception)
def handle_unexpected_error(e: Exception):
    logger.exception("Unhandled exception | request_id=%s", _request_id())
    return _error(500, "Server error")


@bp.get("/health")
def health():
    return jsonify({"status": "ok", "request_id": _request_id()}), 200


@bp.post("/classes")
def post_class():
    try:
        payload = AddClassRequest.model_validate(request.get_json())
    except ValidationError as e:
        return _validation_error(e)

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
        # e.g. "Class already exists"
        logger.info(
            "class create rejected | request_id=%s | code=%s euid=%s reason=%s",
            _request_id(),
            payload.code,
            payload.euid,
            str(e),
        )
        return _error(409, str(e))

    logger.info(
        "class created | request_id=%s | code=%s euid=%s sessions_created=%s",
        _request_id(),
        payload.code,
        payload.euid,
        created,
    )
    return (
        jsonify({"status": "success", "sessions_created": created, "request_id": _request_id()}),
        201,
    )


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

    if result.status == "success":
        logger.info(
            "attendance accepted | request_id=%s | code=%s euid=%s",
            _request_id(),
            payload.code,
            payload.euid,
        )
        return jsonify({"status": "success", "request_id": _request_id()}), 200

    logger.info(
        "attendance rejected | request_id=%s | code=%s euid=%s reason=%s",
        _request_id(),
        payload.code,
        payload.euid,
        result.error,
    )
    # Keep it 400 for now; later we can map specific errors to 401/403/404/etc.
    return _error(400, result.error or "Attendance rejected")


@bp.get("/students/<euid>/attendance")
def get_student_attendance(euid: str):
    try:
        payload = GetStudentAttendanceRequest.model_validate({"euid": euid})
    except ValidationError as e:
        return _validation_error(e)

    db = get_db()
    rows = repository.get_student_attendance(db, student_euid=payload.euid)
    return jsonify({"status": "success", "attendance": rows, "request_id": _request_id()}), 200


@bp.get("/classes/<code>/attendance")
def get_class_attendance(code: str):
    try:
        payload = GetClassAttendanceRequest.model_validate({"code": code})
    except ValidationError as e:
        return _validation_error(e)

    db = get_db()
    rows = repository.get_class_attendance(db, code=payload.code)
    return jsonify({"status": "success", "attendance": rows, "request_id": _request_id()}), 200


@bp.get("/classes/<code>/schedule")
def get_class_schedule(code: str):
    try:
        payload = GetClassScheduleRequest.model_validate({"code": code})
    except ValidationError as e:
        return _validation_error(e)

    db = get_db()
    rows = repository.get_class_schedule(db, code=payload.code)
    return jsonify({"status": "success", "days": rows, "request_id": _request_id()}), 200


@bp.get("/professors/<euid>/schedule")
def get_professor_schedule(euid: str):
    try:
        payload = GetProfessorScheduleRequest.model_validate({"euid": euid})
    except ValidationError as e:
        return _validation_error(e)

    db = get_db()
    rows = repository.get_professor_schedule(db, professor_euid=payload.euid)
    return jsonify({"status": "success", "classes": rows, "request_id": _request_id()}), 200


@bp.get("/professors/<euid>/classes")
def get_professor_class_codes(euid: str):
    try:
        payload = GetProfessorClassCodesRequest.model_validate({"euid": euid})
    except ValidationError as e:
        return _validation_error(e)

    db = get_db()
    codes = repository.get_professor_class_codes(db, professor_euid=payload.euid)
    return jsonify({"status": "success", "codes": codes, "request_id": _request_id()}), 200
