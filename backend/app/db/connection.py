from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import current_app, g


def _db_path() -> Path:
    cfg = current_app.config["APP_CONFIG"]
    return Path(cfg.database_path).resolve()


def get_db() -> sqlite3.Connection:
    """
    Returns a per-request SQLite connection stored in Flask's `g`.
    """
    if "db" not in g:
        path = _db_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row

        # Ensure foreign keys are enforced per connection
        conn.execute("PRAGMA foreign_keys = ON;")

        g.db = conn
    return g.db


def close_db(_: BaseException | None = None) -> None:
    """
    Closes the per-request SQLite connection (if present).
    Called automatically by Flask appcontext teardown.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    """
    Initializes the database using schema.sql.
    Must be called inside an application context.
    """
    db = get_db()
    schema_path = Path(current_app.root_path) / "db" / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")
    db.executescript(schema_sql)
    db.commit()
