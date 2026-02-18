from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.db import repository


def _init_test_db(db: sqlite3.Connection) -> None:
    """
    Loads the project's schema.sql into this sqlite connection.
    """
    schema_path = Path(__file__).resolve().parents[1] / "app" / "db" / "schema.sql"
    db.executescript(schema_path.read_text(encoding="utf-8"))
    db.commit()


@pytest.fixture()
def db(tmp_path: Path) -> sqlite3.Connection:
    """
    Returns a fresh sqlite db connection per test, backed by a temp file.
    """
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    _init_test_db(conn)

    yield conn

    conn.close()


def test_generate_sessions_monday_wednesday_inclusive(db: sqlite3.Connection) -> None:
    # Arrange: create a class (sessions depend on FK)
    repository.insert_class_info(
        db,
        code="csce_4901_501",
        professor_euid="gdb0100",
        lat=33.0,
        lon=-97.0,
        start_date="2025-04-01",
        end_date="2025-04-15",
    )

    times = {
        "Monday": "09:00:00",
        "Wednesday": "09:00:00",
    }

    # Act
    created = repository.generate_sessions(
        db,
        code="csce_4901_501",
        start_date="2025-04-01",
        end_date="2025-04-15",
        times=times,
    )
    db.commit()

    # Assert count (April 1–15, 2025 includes:
    # Wed 2, Mon 7, Wed 9, Mon 14 = 4 sessions)
    assert created == 4

    rows = repository.get_class_schedule(db, code="csce_4901_501")
    assert len(rows) == 4

    dates = [r["date"] for r in rows]
    assert dates == ["2025-04-02", "2025-04-07", "2025-04-09", "2025-04-14"]

    # All should have the chosen time
    assert all(r["time"] == "09:00:00" for r in rows)


def test_generate_sessions_rejects_end_before_start(db: sqlite3.Connection) -> None:
    repository.insert_class_info(
        db,
        code="csce_4901_501",
        professor_euid="gdb0100",
        lat=33.0,
        lon=-97.0,
        start_date="2025-04-10",
        end_date="2025-04-01",
    )

    with pytest.raises(ValueError, match="end_date must be >="):
        repository.generate_sessions(
            db,
            code="csce_4901_501",
            start_date="2025-04-10",
            end_date="2025-04-01",
            times={"Monday": "09:00:00"},
        )


def test_generate_sessions_requires_at_least_one_day(db: sqlite3.Connection) -> None:
    repository.insert_class_info(
        db,
        code="csce_4901_501",
        professor_euid="gdb0100",
        lat=33.0,
        lon=-97.0,
        start_date="2025-04-01",
        end_date="2025-04-15",
    )

    with pytest.raises(ValueError, match="at least one weekday"):
        repository.generate_sessions(
            db,
            code="csce_4901_501",
            start_date="2025-04-01",
            end_date="2025-04-15",
            times={},
        )
