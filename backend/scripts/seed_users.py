from __future__ import annotations

import os
from app.factory import create_app
from app.services.auth_service import register_user

DEFAULT_USERS = [
    ("pro1234", "password123", "professor"),
    ("stu1234", "password123", "student"),
]

def main() -> None:
    app = create_app()
    with app.app_context():
        for euid, password, role in DEFAULT_USERS:
            try:
                register_user(euid=euid, password=password, role=role)
                print(f"Created user: {euid} ({role})")
            except Exception as e:
                # likely "UNIQUE constraint failed" if already exists
                print(f"Skipped {euid}: {e}")

if __name__ == "__main__":
    main()