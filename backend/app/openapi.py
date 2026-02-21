from __future__ import annotations

from typing import Any

from flask import Flask, jsonify
from flask_swagger_ui import get_swaggerui_blueprint


def _openapi_spec() -> dict[str, Any]:
    """
    A pragmatic, hand-authored OpenAPI spec that matches our current routes.
    This keeps the project lightweight and avoids coupling route code to a specific OpenAPI framework.
    """
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Attendance Face API",
            "version": "1.0.0",
            "description": (
                "Flask API for attendance verification using face recognition, schedule validation, "
                "GPS distance checks, and time window enforcement. Includes JWT auth  RBAC  refresh tokens."
            ),
        },
        "servers": [{"url": "/"}],
        "tags": [
            {"name": "Health"},
            {"name": "Auth"},
            {"name": "Classes"},
            {"name": "Attendance"},
            {"name": "Schedules"},
        ],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Use an access token: Authorization: Bearer <token>",
                }
            },
            "schemas": {
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "error"},
                        "error": {"type": "string"},
                        "request_id": {"type": "string"},
                        "details": {"type": "array", "items": {"type": "object"}},
                    },
                    "required": ["status", "error", "request_id"],
                },
                "LoginRequest": {
                    "type": "object",
                    "properties": {
                        "euid": {"type": "string", "example": "stu1234"},
                        "password": {"type": "string", "example": "password123"},
                    },
                    "required": ["euid", "password"],
                },
                "LoginResponse": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "success"},
                        "access_token": {"type": "string"},
                        "refresh_token": {"type": "string"},
                        "request_id": {"type": "string"},
                    },
                    "required": ["status", "access_token", "refresh_token"],
                },
                "RefreshRequest": {
                    "type": "object",
                    "properties": {"refresh_token": {"type": "string"}},
                    "required": ["refresh_token"],
                },
                "RefreshResponse": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "success"},
                        "access_token": {"type": "string"},
                        "refresh_token": {"type": "string"},
                        "request_id": {"type": "string"},
                    },
                    "required": ["status", "access_token", "refresh_token"],
                },
                "AddClassRequest": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "example": "csce_4900_500"},
                        "euid": {"type": "string", "example": "pro1234"},
                        "location": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 2,
                            "maxItems": 2,
                            "example": [33.214, -97.133],
                        },
                        "start_date": {"type": "string", "example": "2025-04-01"},
                        "end_date": {"type": "string", "example": "2025-04-15"},
                        "times": {
                            "type": "object",
                            "additionalProperties": {"type": "string"},
                            "example": {"Monday": "09:00:00", "Wednesday": "09:00:00"},
                        },
                    },
                    "required": ["code", "euid", "location", "start_date", "end_date", "times"],
                },
                "AddClassResponse": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "success"},
                        "sessions_created": {"type": "integer", "example": 10},
                        "join_code": {"type": "string", "example": "A1B2C3D4"},
                        "request_id": {"type": "string"},
                    },
                    "required": ["status", "sessions_created"],
                },
                "StudentEnrollRequest": {
                    "type": "object",
                    "properties": {
                        "euid": {"type": "string", "example": "stu1234"},
                        "code": {"type": "string", "example": "csce_4900_500"},
                        "join_code": {"type": "string", "example": "A1B2C3D4"},
                        "photo": {"type": "string", "description": "Base64-encoded image"},
                    },
                    "required": ["euid", "code", "join_code", "photo"],
                },
                "FaceLoginRequest": {
                    "type": "object",
                    "properties": {
                        "euid": {"type": "string", "example": "stu1234"},
                        "photo": {"type": "string", "description": "Base64-encoded image"},
                    },
                    "required": ["euid", "photo"],
                },
                "AddAttendanceRequest": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "example": "csce_4900_500"},
                        "euid": {"type": "string", "example": "stu1234"},
                        "location": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 2,
                            "maxItems": 2,
                            "example": [33.214, -97.133],
                        },
                        "photo": {"type": "string", "description": "Base64-encoded image"},
                    },
                    "required": ["code", "euid", "location", "photo"],
                },
                "SuccessResponse": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "success"},
                        "request_id": {"type": "string"},
                    },
                    "required": ["status"],
                },
                "StudentAttendanceResponse": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "success"},
                        "attendance": {"type": "array", "items": {"type": "object"}},
                        "request_id": {"type": "string"},
                    },
                    "required": ["status", "attendance"],
                },
                "ProfessorScheduleResponse": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "success"},
                        "classes": {"type": "array", "items": {"type": "object"}},
                        "request_id": {"type": "string"},
                    },
                    "required": ["status", "classes"],
                },
                "ClassScheduleResponse": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "success"},
                        "days": {"type": "array", "items": {"type": "object"}},
                        "request_id": {"type": "string"},
                    },
                    "required": ["status", "days"],
                },
                "ClassAttendanceResponse": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "success"},
                        "attendance": {"type": "array", "items": {"type": "object"}},
                        "request_id": {"type": "string"},
                    },
                    "required": ["status", "attendance"],
                },
            },
        },
        "paths": {
            "/health": {
                "get": {
                    "tags": ["Health"],
                    "summary": "Health check",
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SuccessResponse"}}},
                        }
                    },
                }
            },
            "/auth/login": {
                "post": {
                    "tags": ["Auth"],
                    "summary": "Login (issue access  refresh tokens)",
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/LoginRequest"}}},
                    },
                    "responses": {
                        "200": {
                            "description": "Tokens issued",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/LoginResponse"}}},
                        },
                        "400": {"description": "Missing credentials", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                        "401": {"description": "Invalid credentials", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    },
                }
            },
            "/auth/refresh": {
                "post": {
                    "tags": ["Auth"],
                    "summary": "Refresh tokens (rotating refresh token)",
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/RefreshRequest"}}},
                    },
                    "responses": {
                        "200": {
                            "description": "New token pair",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/RefreshResponse"}}},
                        },
                        "400": {"description": "Missing refresh token", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                        "401": {"description": "Invalid refresh token", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    },
                }
            },
            "/auth/enroll": {
                "post": {
                    "tags": ["Auth"],
                    "summary": "Student self-enroll using join code + reference face; returns tokens",
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/StudentEnrollRequest"}}},
                    },
                    "responses": {
                        "200": {"description": "Tokens issued", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/LoginResponse"}}}},
                        "400": {"description": "Validation error", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                        "401": {"description": "Invalid join code / enrollment failed", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    },
                }
            },
            "/auth/face-login": {
                "post": {
                    "tags": ["Auth"],
                    "summary": "Student face login (no password); returns tokens",
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/FaceLoginRequest"}}},
                    },
                    "responses": {
                        "200": {"description": "Tokens issued", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/LoginResponse"}}}},
                        "400": {"description": "Validation error", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                        "401": {"description": "Face login failed", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    },
                }
            },
            "/classes": {
                "post": {
                    "tags": ["Classes"],
                    "summary": "Create a class (professor only, self only)",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AddClassRequest"}}},
                    },
                    "responses": {
                        "201": {
                            "description": "Created",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AddClassResponse"}}},
                        },
                        "400": {"description": "Validation error", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                        "401": {"description": "Missing/invalid token", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                        "403": {"description": "Forbidden", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                        "409": {"description": "Conflict", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    },
                }
            },
            "/classes/{code}/join-code/rotate": {
                "post": {
                    "tags": ["Classes"],
                    "summary": "Rotate a class join code (professor only, must own class)",
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {"name": "code", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {
                            "description": "Rotated",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "success"},
                                            "join_code": {"type": "string", "example": "Z9Y8X7W6"},
                                            "request_id": {"type": "string"},
                                        },
                                    }
                                }
                            },
                        },
                        "401": {"description": "Missing/invalid token", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                        "403": {"description": "Forbidden", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    },
                }
            },
            "/attendance": {
                "post": {
                    "tags": ["Attendance"],
                    "summary": "Submit attendance (student only, self only)",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AddAttendanceRequest"}}},
                    },
                    "responses": {
                        "200": {"description": "Accepted", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SuccessResponse"}}}},
                        "400": {"description": "Rejected/validation error", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                        "401": {"description": "Missing/invalid token", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                        "403": {"description": "Forbidden", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    },
                }
            },
            "/students/{euid}/attendance": {
                "get": {
                    "tags": ["Attendance"],
                    "summary": "Get a student's attendance (student only, self only)",
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {"name": "euid", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {"description": "OK", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/StudentAttendanceResponse"}}}},
                        "400": {"description": "Validation error", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                        "401": {"description": "Missing/invalid token", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                        "403": {"description": "Forbidden", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    },
                }
            },
            "/classes/{code}/attendance": {
                "get": {
                    "tags": ["Attendance"],
                    "summary": "Get class attendance by code",
                    "parameters": [
                        {"name": "code", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {"description": "OK", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ClassAttendanceResponse"}}}},
                        "400": {"description": "Validation error", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    },
                }
            },
            "/classes/{code}/schedule": {
                "get": {
                    "tags": ["Schedules"],
                    "summary": "Get class schedule by code",
                    "parameters": [
                        {"name": "code", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {"description": "OK", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ClassScheduleResponse"}}}},
                        "400": {"description": "Validation error", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    },
                }
            },
            "/professors/{euid}/schedule": {
                "get": {
                    "tags": ["Schedules"],
                    "summary": "Get professor schedule (professor only, self only)",
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {"name": "euid", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {"description": "OK", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ProfessorScheduleResponse"}}}},
                        "400": {"description": "Validation error", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                        "401": {"description": "Missing/invalid token", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                        "403": {"description": "Forbidden", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    },
                }
            },
        },
    }


def register_openapi(app: Flask) -> None:
    """
    Registers:
      - GET /openapi.json  -> OpenAPI 3 spec
      - GET /docs          -> Swagger UI
    """

    @app.get("/openapi.json")
    def openapi_json():
        return jsonify(_openapi_spec())

    swaggerui_bp = get_swaggerui_blueprint(
        "/docs",
        "/openapi.json",
        config={"app_name": "Attendance Face API"},
    )
    app.register_blueprint(swaggerui_bp, url_prefix="/docs")