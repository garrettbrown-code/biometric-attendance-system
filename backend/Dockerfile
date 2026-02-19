# ---- Base image ----
FROM python:3.12-slim

# ---- System dependencies for dlib / face_recognition ----
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
  && rm -rf /var/lib/apt/lists/*


# ---- Working directory ----
WORKDIR /app

# ---- Copy dependency files first (for layer caching) ----
COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy project ----
COPY . .

# ---- Environment defaults ----
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

# ---- Run app ----
CMD ["python", "run.py"]
