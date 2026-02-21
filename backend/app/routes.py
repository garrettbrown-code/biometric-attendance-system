from __future__ import annotations

import logging
import json
import uuid

from datetime import datetime, timezone
from flask import Blueprint, current_app, g, jsonify, request
from pydantic import ValidationError

from app.config import Config
from app.db import repository
from app.db.connection import get_db
from app.models.requests import (
    AddAttendanceRequest,
    AddClassRequest,
    FaceLoginRequest,
    EnrollInClassRequest,
    GetClassAttendanceRequest,
    GetClassScheduleRequest,
    GetProfessorClassCodesRequest,
    GetProfessorScheduleRequest,
    GetStudentAttendanceRequest,
    StudentEnrollRequest,
)
from app.services.attendance_service import add_attendance
from app.auth.decorators import jwt_required
from app.services.auth_service import (
    authenticate_user,
    enroll_student_with_join_code,
    face_login_student,
    refresh_access_token,
)

bp = Blueprint("api", __name__)
logger = logging.getLogger(__name__)


def _cfg() -> Config:
    return current_app.config["APP_CONFIG"]


def _request_id() -> str:
    return getattr(g, "request_id", "")


def _json_safe(value):
    """
    Convert arbitrary values into JSON-serializable values.
    Pydantic error contexts can include exception objects (e.g., ValueError).
    """
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _normalize_pydantic_errors(errors: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    for err in errors:
        err = dict(err)
        if "ctx" in err and isinstance(err["ctx"], dict):
            err["ctx"] = {k: _json_safe(v) for k, v in err["ctx"].items()}
        # Defensive: sometimes 'input' can be non-serializable too
        if "input" in err:
            err["input"] = _json_safe(err["input"])
        normalized.append(err)
    return normalized


def _validation_error(e: ValidationError):
    return (
        jsonify(
            {
                "status": "error",
                "error": "Validation error",
                "details": _normalize_pydantic_errors(e.errors()),
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


@bp.post("/auth/login")
def login():
    data = request.get_json() or {}
    euid = data.get("euid")
    password = data.get("password")

    if not euid or not password:
        return _error(400, "Missing credentials")

    cfg = _cfg()
    tokens = authenticate_user(euid=euid, password=password, cfg=cfg)

    if not tokens:
        return _error(401, "Invalid credentials")

    return jsonify({"status": "success", **tokens}), 200


@bp.post("/auth/refresh")
def refresh():
    data = request.get_json() or {}
    refresh_token = data.get("refresh_token")

    if not refresh_token:
        return _error(400, "Missing refresh token")

    cfg = _cfg()
    tokens = refresh_access_token(refresh_token=refresh_token, cfg=cfg)

    if not tokens:
        return _error(401, "Invalid refresh token")

    return jsonify({"status": "success", **tokens}), 200


@bp.post("/classes/<code>/join-code/rotate")
@jwt_required(role="professor")
def rotate_join_code(code: str):
    db = get_db()

    # Verify ownership
    if not repository.professor_exists_for_class(db, code=code, professor_euid=g.current_user):
        return _error(403, "Forbidden")

    new_code = repository.generate_join_code()
    now_iso = datetime.now(timezone.utc).isoformat()

    db.execute(
        """
        UPDATE tbl_class_info
        SET fld_ci_join_code = ?, fld_ci_join_code_created_at = ?
        WHERE fld_ci_code_pk = ?
        """,
        (new_code, now_iso, code),
    )
    db.commit()

    return jsonify({
        "status": "success",
        "join_code": new_code,
        "request_id": _request_id(),
    }), 200


@bp.post("/classes")
@jwt_required(role="professor")
def post_class():
    try:
        payload = AddClassRequest.model_validate(request.get_json())
        if payload.euid != g.current_user:
            return _error(403, "Forbidden")
    except ValidationError as e:
        return _validation_error(e)

    db = get_db()
    join_code = repository.generate_join_code()
    join_code_created_at = datetime.now(timezone.utc).isoformat()

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
            join_code=join_code,
            join_code_created_at=join_code_created_at,
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
        jsonify(
            {
                "status": "success",
                "sessions_created": created,
                "join_code": join_code,
                "request_id": _request_id(),
            }
        ),
        201,
    )


@bp.post("/auth/enroll")
def enroll():
    try:
        payload = StudentEnrollRequest.model_validate(request.get_json())
    except ValidationError as e:
        return _validation_error(e)

    db = get_db()
    cfg = _cfg()
    tokens = enroll_student_with_join_code(
        db=db,
        cfg=cfg,
        euid=payload.euid,
        code=payload.code,
        join_code=payload.join_code,
        photo_b64=payload.photo,
    )
    if not tokens:
        return _error(401, "Invalid join code or enrollment failed")

    return jsonify({"status": "success", **tokens, "request_id": _request_id()}), 200


@bp.post("/auth/face-login")
def face_login():
    try:
        payload = FaceLoginRequest.model_validate(request.get_json())
    except ValidationError as e:
        return _validation_error(e)

    db = get_db()
    cfg = _cfg()
    tokens = face_login_student(db=db, cfg=cfg, euid=payload.euid, photo_b64=payload.photo)
    if not tokens:
        return _error(401, "Face login failed")

    return jsonify({"status": "success", **tokens, "request_id": _request_id()}), 200


@bp.post("/attendance")
@jwt_required(role="student")
def post_attendance():
    try:
        payload = AddAttendanceRequest.model_validate(request.get_json())
        if payload.euid != g.current_user:
            return _error(403, "Forbidden")
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


@bp.post("/students/me/classes")
@jwt_required(role="student")
def enroll_in_class():
    """
    Enroll the authenticated student in a class by code.
    """
    try:
        payload = EnrollInClassRequest.model_validate(request.get_json())
    except ValidationError as e:
        return _validation_error(e)

    db = get_db()
    student_euid = g.current_user

    try:
        repository.enroll_student_in_class(db, student_euid=student_euid, code=payload.code)
        db.commit()
    except ValueError as e:
        msg = str(e)
        if msg == "Class not found":
            return _error(404, msg)
        if msg == "Already enrolled":
            return _error(409, msg)
        return _error(400, msg)

    return jsonify({"status": "success", "request_id": _request_id()}), 201


@bp.get("/students/me/classes")
@jwt_required(role="student")
def get_my_classes():
    db = get_db()
    rows = repository.get_student_classes(db, student_euid=g.current_user)
    return jsonify({"status": "success", "classes": rows, "request_id": _request_id()}), 200


@bp.get("/students/me/attendance")
@jwt_required(role="student")
def get_my_attendance():
    """
    Mobile-friendly alias for the authenticated student's attendance history.
    """
    db = get_db()
    rows = repository.get_student_attendance(db, student_euid=g.current_user)
    return jsonify({"status": "success", "attendance": rows, "request_id": _request_id()}), 200


# Legacy / Debug
@bp.get("/students/<euid>/attendance")
@jwt_required(role="student")
def get_student_attendance(euid: str):
    try:
        payload = GetStudentAttendanceRequest.model_validate({"euid": euid})
        if g.current_user != euid:
            return _error(403, "Forbidden")
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
@jwt_required(role="professor")
def get_professor_schedule(euid: str):
    if g.current_user != euid:
        return _error(403, "Forbidden")
    try:
        payload = GetProfessorScheduleRequest.model_validate({"euid": euid})
    except ValidationError as e:
        return _validation_error(e)

    db = get_db()
    rows = repository.get_professor_schedule(db, professor_euid=payload.euid)
    return jsonify({"status": "success", "classes": rows, "request_id": _request_id()}), 200


@bp.get("/professors/<euid>/classes")
@jwt_required(role="professor")
def get_professor_class_codes(euid: str):
    if g.current_user != euid:
        return _error(403, "Forbidden")
    try:
        payload = GetProfessorClassCodesRequest.model_validate({"euid": euid})
    except ValidationError as e:
        return _validation_error(e)

    db = get_db()
    codes = repository.get_professor_class_codes(db, professor_euid=payload.euid)
    return jsonify({"status": "success", "codes": codes, "request_id": _request_id()}), 200
