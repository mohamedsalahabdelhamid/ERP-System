# syntax=docker/dockerfile:1

# ============================================================
# ERP backend image (FastAPI + Uvicorn)
# ============================================================
# slim-bookworm is a stable Debian base. No apt/system packages are installed:
# every Python dependency ships a binary wheel for 3.12, so the image is fully
# self-contained and never touches Debian mirrors at build or run time.
FROM python:3.12-slim-bookworm AS base

# Keep Python lean and predictable inside containers.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install Python dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application source.
COPY . .

# Run as a non-root user.
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Default command: run the API. In compose we wrap this with an entrypoint
# that waits for the DB and applies migrations first.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
