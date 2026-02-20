# Authentication & Authorization

This project implements production-style JWT authentication with rotating refresh tokens and role-based access control.

---

## Overview

The system uses:

- bcrypt password hashing
- Short-lived access tokens
- Rotating refresh tokens
- Role-based access control (RBAC)
- Resource-level ownership enforcement

---

## Token Types

### Access Token

Short-lived JWT used for API access.

Claims:

- sub (user identifier)
- role (student or professor)
- type = "access"
- jti (unique token ID)
- iat
- exp

Used in:

Authorization: Bearer <access_token>

---

### Refresh Token

Long-lived JWT stored in database.

Claims:

- sub
- type = "refresh"
- jti
- iat
- exp

Used only for:

POST /auth/refresh

---

## Login Flow

1. User submits credentials
2. Password verified via bcrypt
3. Access token issued
4. Refresh token issued
5. Refresh token stored in database

---

## Refresh Flow (Rotation)

When refreshing:

1. Validate refresh JWT signature
2. Confirm token exists in database
3. Confirm not revoked
4. Confirm not expired
5. Revoke old refresh token
6. Issue new refresh token
7. Issue new access token
8. Persist new refresh token

This prevents replay attacks.

---

## RBAC

Roles:

- student
- professor

Enforced via:

@jwt_required(role="professor")

---

## Ownership Enforcement

Students can only access:

GET /students/<their_euid>/attendance

Professors can only:

- Create classes for themselves

- View their own schedule

Prevents horizontal privilege escalation.

---

## Password Storage

Passwords are hashed using bcrypt.

Passwords are never stored or logged in plaintext.

---

## Why This Matters

This is production-grade authentication design:

- Stateless access tokens

- Stateful refresh tokens

- Token revocation

- Token rotation

- Clear separation of concerns