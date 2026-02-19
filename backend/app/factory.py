from __future__ import annotations

import logging

from dotenv import load_dotenv
from flask import Flask

from app.config import Config
from app.db.connection import close_db
from app.routes import bp as api_bp


def _configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def create_app() -> Flask:
    load_dotenv()
    cfg = Config()
    _configure_logging(cfg.log_level)

    app = Flask(__name__)
    app.config["APP_CONFIG"] = cfg
    app.register_blueprint(api_bp)

    app.teardown_appcontext(close_db)

    return app
