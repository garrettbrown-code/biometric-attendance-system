# Security Model

This document describes the threat model and protections implemented.

---

## Threats Addressed

### 1. Unauthorized API Access
Mitigated via JWT authentication.

### 2. Horizontal Privilege Escalation
Mitigated via self-access enforcement.

### 3. Token Replay Attacks
Mitigated via refresh token rotation.

### 4. Stolen Refresh Tokens
Mitigated via revocation flag in database.

### 5. Expired Tokens
Mitigated via JWT expiration and DB expiration checks.

---

## Defense-in-Depth Strategy

1. JWT signature validation
2. Role enforcement
3. Ownership enforcement
4. Token expiration
5. Refresh rotation
6. Revocation support

---

## Security Design Principles

- Least privilege
- Explicit role checks
- Stateless access tokens
- Stateful refresh tokens
- Clear separation of concerns
- No business logic in routes

---

## Future Enhancements

- Rate limiting
- Audit logging
- Multi-factor authentication
- OAuth provider support
- IP anomaly detection
- Production WSGI deployment hardening