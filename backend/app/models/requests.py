from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.validation import (
    WEEKDAYS,
    validate_base64_image,
    validate_class_code,
    validate_date_yyyymmdd,
    validate_euid,
    validate_location,
    validate_time_hhmmss,
)


class AddClassRequest(BaseModel):
    code: str = Field(..., description="abcd_1234_123")
    euid: str = Field(..., description="abc1234 (professor EUID)")
    location: tuple[float, float] = Field(..., description="(lat, lon)")
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")
    times: dict[str, str] = Field(..., description="weekday -> HH:MM:SS")

    @field_validator("code")
    @classmethod
    def _code(cls, v: str) -> str:
        return validate_class_code(v)

    @field_validator("euid")
    @classmethod
    def _euid(cls, v: str) -> str:
        return validate_euid(v)

    @field_validator("location", mode="before")
    @classmethod
    def _location(cls, v):
        return validate_location(v)

    @field_validator("start_date", "end_date")
    @classmethod
    def _date(cls, v: str) -> str:
        return validate_date_yyyymmdd(v)

    @field_validator("times")
    @classmethod
    def _times(cls, v: dict[str, str]) -> dict[str, str]:
        if not isinstance(v, dict) or len(v) == 0:
            raise ValueError("times must be a non-empty object of weekday -> time")
        cleaned: dict[str, str] = {}
        for day, t in v.items():
            if day not in WEEKDAYS:
                raise ValueError(f"Invalid weekday: {day!r}")
            cleaned[day] = validate_time_hhmmss(t)
        return cleaned

    @model_validator(mode="after")
    def _date_order(self):
        from datetime import datetime

        start = datetime.strptime(self.start_date, "%Y-%m-%d").date()
        end = datetime.strptime(self.end_date, "%Y-%m-%d").date()
        if end < start:
            raise ValueError("end_date must be >= start_date")
        return self


class EnrollInClassRequest(BaseModel):
    code: str = Field(..., description="abcd_1234_123")

    @field_validator("code")
    @classmethod
    def _code(cls, v: str) -> str:
        return validate_class_code(v)


class AddAttendanceRequest(BaseModel):
    code: str
    euid: str
    location: tuple[float, float]
    photo: str

    @field_validator("code")
    @classmethod
    def _code(cls, v: str) -> str:
        return validate_class_code(v)

    @field_validator("euid")
    @classmethod
    def _euid(cls, v: str) -> str:
        return validate_euid(v)

    @field_validator("location", mode="before")
    @classmethod
    def _location(cls, v):
        return validate_location(v)

    @field_validator("photo")
    @classmethod
    def _photo(cls, v: str) -> str:
        return validate_base64_image(v)


class GetStudentAttendanceRequest(BaseModel):
    euid: str

    @field_validator("euid")
    @classmethod
    def _euid(cls, v: str) -> str:
        return validate_euid(v)


class GetClassAttendanceRequest(BaseModel):
    code: str

    @field_validator("code")
    @classmethod
    def _code(cls, v: str) -> str:
        return validate_class_code(v)


class GetClassScheduleRequest(BaseModel):
    code: str

    @field_validator("code")
    @classmethod
    def _code(cls, v: str) -> str:
        return validate_class_code(v)


class GetProfessorScheduleRequest(BaseModel):
    euid: str

    @field_validator("euid")
    @classmethod
    def _euid(cls, v: str) -> str:
        return validate_euid(v)


class GetProfessorClassCodesRequest(BaseModel):
    euid: str

    @field_validator("euid")
    @classmethod
    def _euid(cls, v: str) -> str:
        return validate_euid(v)


# Optional: user enrollment/photo management later
class AddUserRequest(BaseModel):
    user_type: Literal["Student", "Professor"]
    euid: str

    @field_validator("euid")
    @classmethod
    def _euid(cls, v: str) -> str:
        return validate_euid(v)


class AddPhotoRequest(BaseModel):
    user_type: Literal["Student", "Professor"]
    euid: str
    photo: str

    @field_validator("euid")
    @classmethod
    def _euid(cls, v: str) -> str:
        return validate_euid(v)

    @field_validator("photo")
    @classmethod
    def _photo(cls, v: str) -> str:
        return validate_base64_image(v)
