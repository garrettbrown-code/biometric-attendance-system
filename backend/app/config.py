from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _get_env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as e:
        raise ValueError(f"Environment variable {name} must be an integer, got: {raw!r}") from e


@dataclass(frozen=True)
class Config:
    # App
    flask_env: str = os.getenv("FLASK_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Server
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = _get_env_int("PORT", 8000)

    # Database
    database_path: str = os.getenv("DATABASE_PATH", "attendance.db")

    # Attendance policy
    max_distance_feet: int = _get_env_int("MAX_DISTANCE_FEET", 30)
    time_window_minutes: int = _get_env_int("TIME_WINDOW_MINUTES", 30)

    # User storage
    user_data_dir: Path = Path(os.getenv("USER_DATA_DIR", "./data/users")).resolve()

    # Face recognition knobs (optional)
    # face_tolerance: float = float(os.getenv("FACE_TOLERANCE", "0.6"))

    @property
    def is_production(self) -> bool:
        return self.flask_env.lower() == "production"
