from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    status: str = "error"
    error: str
    details: Any | None = None


class SuccessResponse(BaseModel):
    status: str = "success"


class AddClassResponse(SuccessResponse):
    sessions_created: int


class AttendanceQueryRow(BaseModel):
    code: str
    date: str
    time: str


class StudentAttendanceResponse(SuccessResponse):
    attendance: list[AttendanceQueryRow]
