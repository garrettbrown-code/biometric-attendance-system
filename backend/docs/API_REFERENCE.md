# API Reference

All responses include:

- status
- request_id

---

## Authentication

### POST /auth/login

Request:

{
  "euid": "stu1234",
  "password": "password123"
}

Response:

{
  "status": "success",
  "access_token": "...",
  "refresh_token": "..."
}

---

### POST /auth/refresh

Request:

{
  "refresh_token": "..."
}

Response:

{
  "status": "success",
  "access_token": "...",
  "refresh_token": "..."
}

---

## Classes

### POST /classes

Role: professor

Request:

{
  "code": "csce_4900_500",
  "euid": "pro1234",
  "location": [33.214, -97.133],
  "start_date": "2025-04-01",
  "end_date": "2025-04-15",
  "times": {
    "Monday": "09:00:00"
  }
}

Response:

{
  "status": "success",
  "sessions_created": 10
}

---

## Attendance

### POST /attendance

Role: student

Request:

{
  "code": "csce_4900_500",
  "euid": "stu1234",
  "location": [33.214, -97.133],
  "photo": "<base64_image>"
}

Response:

{
  "status": "success"
}

---

### GET /students/<euid>/attendance

Role: student (self only)

Response:

{
  "status": "success",
  "attendance": [...]
}

---

### GET /classes/<code>/schedule

Public

Response:

{
  "status": "success",
  "days": [...]
}

---

### GET /professors/<euid>/schedule

Role: professor (self only)

Response:

{
  "status": "success",
  "classes": [...]
}