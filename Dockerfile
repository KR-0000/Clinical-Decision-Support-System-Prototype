# Use Python 3.11 slim as base.
# slim is a stripped-down Debian image, smaller than the full image,
# but still has apt-get for installing system dependencies.
FROM python:3.11-slim

# Install system dependencies.
# libpq-dev is needed by psycopg2 to connect to Postgres.
# gcc is needed to compile psycopg2 from source if a prebuilt wheel isn't available.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files first, before copying the rest of the code.
# Docker caches layers: if these files haven't changed, Docker reuses the
# cached install layer below and skips reinstalling, which makes rebuilds
# much faster when only application code changes.
COPY pyproject.toml uv.lock* ./

# Install uv, then export your locked dependencies to a plain requirements.txt
# and install with pip. This avoids treating the project itself as an
# installable package (your app uses a flat app/ layout, not a packaged
# library), which is the safest install path for a uv-managed project
# that was never set up with a [build-system] / src layout.
#
# uv export reads pyproject.toml + uv.lock and writes exact pinned versions,
# so the container gets the same dependency versions you tested locally.
RUN pip install --no-cache-dir uv && \
    uv export --no-hashes --format requirements-txt > requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container.
# This layer comes after the dependency install layer, so editing
# application code does not trigger a full reinstall of all packages.
COPY . .

RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Default command: start the API server.
# This is overridden by the worker service in docker-compose.yml and render.yaml.
# 0.0.0.0 makes the server listen on all network interfaces inside the
# container, which is required for Docker's port mapping to work.
# Do not use --reload in production; it is for local development only.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]