from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
import secrets
import string

WEEKDAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}


@dataclass(frozen=True)
class SessionRow:
    id: int
    code: str
    session_date: str  # YYYY-MM-DD
    session_time: str  # HH:MM:SS


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


# -------------------------
# Existence checks
# -------------------------


def class_exists(db: sqlite3.Connection, code: str) -> bool:
    cur = db.execute("SELECT 1 FROM tbl_class_info WHERE fld_ci_code_pk = ? LIMIT 1", (code,))
    return cur.fetchone() is not None


def professor_exists_for_class(db: sqlite3.Connection, code: str, professor_euid: str) -> bool:
    cur = db.execute(
        "SELECT 1 FROM tbl_class_info WHERE fld_ci_code_pk = ? AND fld_ci_euid = ? LIMIT 1",
        (code, professor_euid),
    )
    return cur.fetchone() is not None


def generate_join_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_join_code(db: sqlite3.Connection, *, code: str) -> dict[str, Any] | None:
    cur = db.execute(
        """
        SELECT fld_ci_join_code AS join_code, fld_ci_join_code_created_at AS created_at
        FROM tbl_class_info
        WHERE fld_ci_code_pk = ?
        """,
        (code,),
    )
    row = cur.fetchone()
    return dict(row) if row else None

def verify_join_code(db: sqlite3.Connection, *, code: str, join_code: str) -> bool:
    cur = db.execute(
        """
        SELECT 1
        FROM tbl_class_info
        WHERE fld_ci_code_pk = ? AND fld_ci_join_code = ?
        LIMIT 1
        """,
        (code, join_code),
    )
    return cur.fetchone() is not None

def enroll_student(db: sqlite3.Connection, *, code: str, student_euid: str) -> None:
    db.execute(
        """
        INSERT OR IGNORE INTO tbl_students (fld_st_code_fk, fld_st_euid)
        VALUES (?, ?)
        """,
        (code, student_euid),
    )

# -------------------------
# Student enrollment
# -------------------------

def student_is_enrolled(db: sqlite3.Connection, *, student_euid: str, code: str) -> bool:
    cur = db.execute(
        """
        SELECT 1
        FROM tbl_students
        WHERE fld_st_euid = ? AND fld_st_code_fk = ?
        LIMIT 1
        """,
        (student_euid, code),
    )
    return cur.fetchone() is not None


def enroll_student_in_class(db: sqlite3.Connection, *, student_euid: str, code: str) -> None:
    """
    Enroll a student in a class.
    Raises:
      - ValueError("Class not found") if class code doesn't exist
      - ValueError("Already enrolled") if enrollment row already exists
    """
    if not class_exists(db, code):
        raise ValueError("Class not found")

    if student_is_enrolled(db, student_euid=student_euid, code=code):
        raise ValueError("Already enrolled")

    db.execute(
        "INSERT INTO tbl_students (fld_st_code_fk, fld_st_euid) VALUES (?, ?)",
        (code, student_euid),
    )


def get_student_classes(db: sqlite3.Connection, *, student_euid: str) -> list[dict[str, Any]]:
    """
    Returns class list for a student (includes professor + date range + location).
    """
    cur = db.execute(
        """
        SELECT
          i.fld_ci_code_pk AS code,
          i.fld_ci_euid AS professor_euid,
          i.fld_ci_start_date AS start_date,
          i.fld_ci_end_date AS end_date,
          i.fld_ci_lat AS lat,
          i.fld_ci_lon AS lon
        FROM tbl_students st
        JOIN tbl_class_info i ON st.fld_st_code_fk = i.fld_ci_code_pk
        WHERE st.fld_st_euid = ?
        ORDER BY i.fld_ci_code_pk ASC
        """,
        (student_euid,),
    )
    return [dict(row) for row in cur.fetchall()]


# -------------------------
# Class creation
# -------------------------


def insert_class_info(
    db: sqlite3.Connection,
    *,
    code: str,
    professor_euid: str,
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    join_code: str | None = None,
    join_code_created_at: str | None = None,
) -> None:
    """
    Inserts a row into tbl_class_info.

    Backward compatible: join_code fields default automatically so tests that
    don't care about enrollment don't have to pass them.
    """
    if join_code is None:
        join_code = generate_join_code()
    if join_code_created_at is None:
        join_code_created_at = _now_iso_utc()

    db.execute(
        """
        INSERT INTO tbl_class_info (
            fld_ci_code_pk, fld_ci_euid, fld_ci_lat, fld_ci_lon, fld_ci_start_date, fld_ci_end_date,
            fld_ci_join_code, fld_ci_join_code_created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (code, professor_euid, lat, lon, start_date, end_date, join_code, join_code_created_at),
    )


def insert_schedule(db: sqlite3.Connection, *, code: str, times: dict[str, str]) -> None:
    # times: {"Monday": "14:00:00", ...}
    for day, t in times.items():
        if day not in WEEKDAYS:
            raise ValueError(f"Invalid weekday: {day!r}")
        db.execute(
            "INSERT INTO tbl_schedule (fld_sc_code_fk, fld_sc_day, fld_sc_time) VALUES (?, ?, ?)",
            (code, day, t),
        )


def generate_sessions(
    db: sqlite3.Connection,
    *,
    code: str,
    start_date: str,
    end_date: str,
    times: dict[str, str],
) -> int:
    """
    Inserts rows into tbl_sessions for each meeting day between start_date and end_date inclusive.
    Returns the number of sessions created.
    """
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

    if end_dt < start_dt:
        raise ValueError("end_date must be >= start_date")

    class_days = set(times.keys())
    if not class_days:
        raise ValueError("times must include at least one weekday")

    created = 0
    current = start_dt
    while current <= end_dt:
        weekday = current.strftime("%A")
        if weekday in class_days:
            session_date = current.strftime("%Y-%m-%d")
            session_time = times[weekday]
            db.execute(
                "INSERT INTO tbl_sessions (fld_se_code_fk, fld_se_date, fld_se_time) VALUES (?, ?, ?)",
                (code, session_date, session_time),
            )
            created += 1
        current += timedelta(days=1)

    return created


def add_class(
    db: sqlite3.Connection,
    *,
    code: str,
    professor_euid: str,
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    times: dict[str, str],
    join_code: str,
    join_code_created_at: str,
) -> int:
    """
    Convenience transaction wrapper for adding a class, schedule, and sessions.
    Returns number of sessions created.
    """
    if class_exists(db, code):
        raise ValueError("Class already exists")

    try:
        insert_class_info(
            db,
            code=code,
            professor_euid=professor_euid,
            lat=lat,
            lon=lon,
            start_date=start_date,
            end_date=end_date,
            join_code=join_code,
            join_code_created_at=join_code_created_at,
        )
        insert_schedule(db, code=code, times=times)
        created = generate_sessions(
            db, code=code, start_date=start_date, end_date=end_date, times=times
        )
        db.commit()
        return created
    except Exception:
        db.rollback()
        raise


# -------------------------
# Attendance / sessions
# -------------------------


def get_session_for_date(db: sqlite3.Connection, *, code: str, on_date: str) -> SessionRow | None:
    """
    Fetches session for a class on a specific date (YYYY-MM-DD).
    Returns None if no session.
    """
    cur = db.execute(
        """
        SELECT fld_se_id_pk, fld_se_code_fk, fld_se_date, fld_se_time
        FROM tbl_sessions
        WHERE fld_se_code_fk = ? AND fld_se_date = ?
        """,
        (code, on_date),
    )
    row = cur.fetchone()
    if row is None:
        return None
    return SessionRow(
        id=row["fld_se_id_pk"],
        code=row["fld_se_code_fk"],
        session_date=row["fld_se_date"],
        session_time=row["fld_se_time"],
    )


def get_class_by_code(db: sqlite3.Connection, *, code: str) -> dict[str, Any] | None:
    """
    Returns class info as a dict:
    {code, professor_euid, lat, lon, start_date, end_date}
    """
    cur = db.execute(
        """
        SELECT
            fld_ci_code_pk AS code,
            fld_ci_euid AS professor_euid,
            fld_ci_lat AS lat,
            fld_ci_lon AS lon,
            fld_ci_start_date AS start_date,
            fld_ci_end_date AS end_date
        FROM tbl_class_info
        WHERE fld_ci_code_pk = ?
        """,
        (code,),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def get_class_location(db: sqlite3.Connection, *, code: str) -> tuple[float, float] | None:
    cur = db.execute(
        "SELECT fld_ci_lat, fld_ci_lon FROM tbl_class_info WHERE fld_ci_code_pk = ?",
        (code,),
    )
    row = cur.fetchone()
    if row is None:
        return None
    return (float(row["fld_ci_lat"]), float(row["fld_ci_lon"]))


def upsert_attendance(
    db: sqlite3.Connection, *, session_id: int, student_euid: str, attended: int
) -> None:
    """
    attended: 1 present, 0 absent
    """
    db.execute(
        """
        INSERT INTO tbl_attendance (fld_at_id_fk, fld_at_euid_fk, fld_at_attended)
        VALUES (?, ?, ?)
        ON CONFLICT(fld_at_id_fk, fld_at_euid_fk)
        DO UPDATE SET fld_at_attended = excluded.fld_at_attended
        """,
        (session_id, student_euid, attended),
    )
    db.commit()


# -------------------------
# Query endpoints
# -------------------------


def get_student_attendance(db: sqlite3.Connection, *, student_euid: str) -> list[dict[str, Any]]:
    cur = db.execute(
        """
        SELECT s.fld_se_code_fk AS code, s.fld_se_date AS date, s.fld_se_time AS time
        FROM tbl_attendance a
        JOIN tbl_sessions s ON a.fld_at_id_fk = s.fld_se_id_pk
        WHERE a.fld_at_euid_fk = ? AND a.fld_at_attended = 1
        ORDER BY s.fld_se_date ASC, s.fld_se_time ASC
        """,
        (student_euid,),
    )
    return [dict(row) for row in cur.fetchall()]


def get_class_attendance(db: sqlite3.Connection, *, code: str) -> list[dict[str, Any]]:
    """
    Returns one row per date: {date: "YYYY-MM-DD", students: "euid1, euid2"}
    """
    cur = db.execute(
        """
        SELECT s.fld_se_date AS date, GROUP_CONCAT(a.fld_at_euid_fk, ', ') AS students
        FROM tbl_sessions s
        JOIN tbl_attendance a ON s.fld_se_id_pk = a.fld_at_id_fk
        WHERE s.fld_se_code_fk = ? AND a.fld_at_attended = 1
        GROUP BY s.fld_se_date
        ORDER BY s.fld_se_date ASC
        """,
        (code,),
    )
    return [dict(row) for row in cur.fetchall()]


def get_class_schedule(db: sqlite3.Connection, *, code: str) -> list[dict[str, Any]]:
    cur = db.execute(
        """
        SELECT fld_se_date AS date, fld_se_time AS time
        FROM tbl_sessions
        WHERE fld_se_code_fk = ?
        ORDER BY fld_se_date ASC, fld_se_time ASC
        """,
        (code,),
    )
    return [dict(row) for row in cur.fetchall()]


def get_professor_schedule(db: sqlite3.Connection, *, professor_euid: str) -> list[dict[str, Any]]:
    cur = db.execute(
        """
        SELECT s.fld_se_code_fk AS code, s.fld_se_date AS date, s.fld_se_time AS time
        FROM tbl_sessions s
        JOIN tbl_class_info i ON s.fld_se_code_fk = i.fld_ci_code_pk
        WHERE i.fld_ci_euid = ?
        ORDER BY s.fld_se_date ASC, s.fld_se_time ASC
        """,
        (professor_euid,),
    )
    return [dict(row) for row in cur.fetchall()]


def get_professor_class_codes(db: sqlite3.Connection, *, professor_euid: str) -> list[str]:
    cur = db.execute(
        """
        SELECT fld_ci_code_pk AS code
        FROM tbl_class_info
        WHERE fld_ci_euid = ?
        ORDER BY fld_ci_code_pk ASC
        """,
        (professor_euid,),
    )
    return [row["code"] for row in cur.fetchall()]
