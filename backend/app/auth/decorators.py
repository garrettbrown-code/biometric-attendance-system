from __future__ import annotations

from functools import wraps
from flask import request, jsonify, current_app, g
from app.auth.jwt_utils import decode_token


def jwt_required(role: str | None = None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"status": "error", "error": "Missing token"}), 401

            token = auth_header.split(" ")[1]
            cfg = current_app.config["APP_CONFIG"]

            try:
                payload = decode_token(
                    token,
                    secret=cfg.jwt_secret_key,
                    algorithm=cfg.jwt_algorithm,
                )
            except Exception:
                return jsonify({"status": "error", "error": "Invalid or expired token"}), 401

            # Reject refresh tokens for protected endpoints
            if payload.get("type") == "refresh":
                return jsonify({"status": "error", "error": "Invalid or expired token"}), 401

            sub = payload.get("sub")
            user_role = payload.get("role")
            if not sub or not user_role:
                return jsonify({"status": "error", "error": "Invalid or expired token"}), 401

            g.current_user = sub
            g.current_role = user_role

            if role and user_role != role:
                return jsonify({"status": "error", "error": "Forbidden"}), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator