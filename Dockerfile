# Use a slim Python base
FROM python:3.14-slim

# Prevent Python from writing pyc files and buffer stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install build deps needed for some packages (cryptography, wheel builds, etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       libssl-dev \
       libffi-dev \
       git \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker layer caching
# Ensure you have a requirements.txt in project root listing FastAPI, uvicorn, sqlalchemy, python-jose[cryptography], passlib[bcrypt], pymysql, alembic, etc.
COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

# Create a non-root user and fix permissions
RUN groupadd -g 1000 app && useradd -m -u 1000 -g app app \
    && chown -R app:app /app

USER app

# Expose the port the app runs on
EXPOSE 8000

# Recommended production command: run uvicorn with multiple workers.
# Adjust workers according to available CPU and project needs.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
