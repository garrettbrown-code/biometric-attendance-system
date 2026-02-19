from __future__ import annotations

import pytest

from app.factory import create_app
from app.config import Config


@pytest.fixture
def app(tmp_path):
    app = create_app()
    app.config["TESTING"] = True

    # Make sure we don’t write to real user directories during tests
    cfg = Config()
    app.config["APP_CONFIG"] = cfg

    return app


@pytest.fixture
def client(app):
    return app.test_client()
