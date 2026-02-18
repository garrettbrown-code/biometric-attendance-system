# Attendance Face API

A Flask-based attendance verification API that validates:
- **Identity** via facial recognition (`face_recognition`)
- **Class** via class code and schedule (SQLite)
- **Location** via GPS distance (Haversine)
- **Timing** via configurable time window relative to class start

This project is intended as a **portfolio / educational** demonstration of backend API design, data modeling, and validation logic.

---

## Features

- Create classes with meeting days/times and auto-generate sessions across a date range
- Record attendance by verifying:
  - class exists and meets today
  - within the configured time window
  - within the configured distance threshold
  - face matches stored reference image (prototype implementation)
- Query attendance:
  - student attendance history
  - class attendance by date
  - class schedule and professor schedule

---

## Architecture (high level)

- **Flask API** handles HTTP requests and responses
- **Service layer** applies attendance rules (time window, distance, identity verification)
- **Repository layer** handles SQLite operations
- **SQLite** stores class info, schedules, generated sessions, and attendance records
- **Face recognition** compares a submitted image to a stored reference image

---

## Privacy & Security Notes (Prototype)

- This project uses facial recognition as a proof-of-concept and **does not include liveness detection**.
  - A photo spoof could pass without additional measures (challenge-response, blink detection, device attestation).
- Reference images should be treated as sensitive data.
- For a production system, prefer storing **face encodings** (not raw images) and implement retention policies.

---

## Tech Stack

- Python 3.11/3.12
- Flask + Waitress
- SQLite
- face_recognition/dlib
- pytest, ruff, black

---

## Setup (WSL / Ubuntu)

### 1) Create and activate a virtual environment

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel

### 2) Install system build dependencies

sudo apt install -y \
  cmake \
  build-essential \
  python3.12-dev \
  pkg-config \
  libopenblas-dev \
  liblapack-dev

### 3) Install runtime dependencies

pip install -r requirements.txt