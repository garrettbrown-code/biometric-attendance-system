from __future__ import annotations

from app import create_app
from app.db.connection import init_db


def main() -> None:
    app = create_app()
    with app.app_context():
        init_db()
    print("Database initialized successfully.")


if __name__ == "__main__":
    main()
