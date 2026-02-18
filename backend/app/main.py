from __future__ import annotations

from waitress import serve

from app.factory import create_app


def main() -> None:
    app = create_app()
    cfg = app.config["APP_CONFIG"]

    # Note: Waitress does NOT terminate TLS by itself.
    # In production, run behind a reverse proxy (nginx/Caddy) for HTTPS.
    serve(app, host=cfg.host, port=cfg.port)


if __name__ == "__main__":
    main()
