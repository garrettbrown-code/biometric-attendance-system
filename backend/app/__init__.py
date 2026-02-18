from __future__ import annotations

import logging
from flask import Flask, jsonify
from dotenv import load_dotenv

from app.config import Config
from app.db.connection import close_db


def _configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def create_app() -> Flask:
    # Loads .env into environment variables for local development.
    load_dotenv()

    cfg = Config()
    _configure_logging(cfg.log_level)

    app = Flask(__name__)
    app.config["APP_CONFIG"] = cfg  # store for easy access

    app.teardown_appcontext(close_db)

    # Minimal route so you can immediately verify the server works.
    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app
