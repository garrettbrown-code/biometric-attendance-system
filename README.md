# Biometric Attendance Platform

A full-stack attendance system that uses server-side facial recognition, geolocation validation, and relational database modeling to securely record classroom attendance.

---

## Overview

This project implements a client-server architecture where students submit a facial image via a mobile application. The backend verifies identity, validates time and location constraints, and records attendance in a normalized relational database.

The system was designed to simulate a real-world production workflow with layered validation and secure API communication.

---

## Architecture

Android Client  
↓ HTTPS (JSON + Base64 image)  
Python Flask Backend  
↓  
SQLite / PostgreSQL Database  

---

## Core Features

### Identity Verification
- Base64 image upload from client
- Server-side decoding and processing
- Facial encoding comparison using `face_recognition`
- Match validation before attendance write

### Validation Layers
- Date validation (class must exist on current date)
- Time-window enforcement (±30 minutes of scheduled class time)
- Geofencing validation (~30 feet) using Haversine distance calculation

### Database Design
- Normalized relational schema
- Foreign key constraints
- Composite primary keys
- CHECK constraints for data integrity
- Idempotent writes using SQLite `ON CONFLICT DO UPDATE`

### API Design
- JSON-based request routing
- Modular function dispatch mapping
- Structured success/error responses
- HTTPS support via Waitress

---

## Tech Stack

- Python
- Flask
- SQLite / PostgreSQL
- Android (client)
- face_recognition (computer vision)
- Haversine (geolocation)
- JSON over HTTPS

---

## Database Schema (Simplified)

- `tbl_class_info`
- `tbl_schedule`
- `tbl_sessions`
- `tbl_students`
- `tbl_attendance`

Designed with relational integrity and separation of concerns in mind.

---

## Running the Backend

### 1. Clone the repository

```
git clone https://github.com/yourusername/biometric-attendance-system.git
cd biometric-attendance-system/backend
```

### 2. Create virtual environment

```
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

### 4. Run the server

```
python app.py
```

Server runs locally at:

```
https://127.0.0.1:8000
```

---

## Future Improvements

- JWT authentication and role-based access control
- Docker containerization
- Object storage for facial images
- Centralized logging
- Unit testing with Pytest
- Deployment to cloud environment

---

## Key Engineering Concepts Demonstrated

- Backend API development
- Relational schema design
- Data validation layers
- Biometric identity workflows
- Idempotent database operations
- Client-server architecture

---

## License

MIT License
