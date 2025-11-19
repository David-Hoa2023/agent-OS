# Codex Prime Agent OS - Production Dockerfile
# Multi-stage build for optimized image size

# Stage 1: Build stage for dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt setup.py ./
COPY codex_prime/__init__.py codex_prime/__init__.py

# Install Python dependencies
RUN pip install --no-cache-dir --user -e .

# Install optional dependencies
RUN pip install --no-cache-dir --user \
    chromadb \
    cryptography \
    websockets \
    uvicorn[standard] \
    fastapi

# Stage 2: Runtime stage
FROM python:3.11-slim

LABEL maintainer="Codex Prime Team"
LABEL description="Codex Prime Agent OS - Autonomous Agent Operating System"
LABEL version="1.0.0"

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 codex && \
    mkdir -p /home/codex/.codex_prime && \
    chown -R codex:codex /home/codex

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/codex/.local

# Copy application code
COPY --chown=codex:codex . /app/

# Set environment variables
ENV PATH=/home/codex/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV CODEX_PRIME_HOME=/home/codex/.codex_prime

# Switch to non-root user
USER codex

# Create necessary directories
RUN mkdir -p \
    /home/codex/.codex_prime/workspace \
    /home/codex/.codex_prime/plugins \
    /home/codex/.codex_prime/logs

# Expose ports
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - run HTTP API server
CMD ["python", "-m", "codex_prime.interfaces.http_server", "--host", "0.0.0.0", "--port", "8000"]
