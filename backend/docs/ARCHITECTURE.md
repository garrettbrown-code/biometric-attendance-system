# Architecture Overview

## High-Level Design

This project follows a layered backend architecture:

routes → services → repository → database

Each layer has a single responsibility and is independently testable.

## Project Structure

app/
├── routes.py # HTTP layer (Flask)
├── services/ # Business logic
│ ├── attendance_service.py
│ └── auth_service.py
├── auth/
│ ├── decorators.py # JWT + RBAC enforcement
│ ├── jwt_utils.py # Token creation / validation
│ └── password_utils.py # bcrypt hashing
├── db/
│ ├── repository.py # Data access layer
│ ├── schema.sql # Database schema
│ └── connection.py
├── models/
│ ├── requests.py # Pydantic request models
│ └── responses.py

---

## Layer Responsibilities

### 1. Routes (HTTP Layer)

Responsible for:

- Request parsing
- Pydantic validation
- Authentication enforcement
- Role enforcement (RBAC)
- Ownership enforcement (self-access rules)
- Structured error responses
- Logging with request IDs

Routes contain **no core business logic**.

---

### 2. Services Layer

Encapsulates domain logic:

- Attendance verification
- Face recognition matching
- Geolocation distance checks
- Time window validation
- Authentication
- Token rotation
- Refresh token revocation

Services are:

- Pure Python
- Easy to unit test
- Independent of Flask

---

### 3. Repository Layer

All SQL is centralized here.

Benefits:

- Clean separation from business logic
- Easier migration to PostgreSQL
- Easier mocking during tests
- Improved maintainability

---

### 4. Database

SQLite is used for simplicity.

Core tables:

- `tbl_users`
- `tbl_refresh_tokens`
- `tbl_classes`
- `tbl_sessions`
- `tbl_attendance`

Foreign keys are enforced.

---

## Security Layers

1. JWT authentication
2. Role-based access control (RBAC)
3. Self-access enforcement
4. Refresh token rotation
5. Token revocation
6. Expiration enforcement
7. Structured error handling

---

## Why This Architecture?

- Mirrors production Flask backend patterns
- Separates concerns clearly
- Easily extensible
- Test-friendly
- Secure by design