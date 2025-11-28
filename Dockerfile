# CollabIQ Production Dockerfile
# Base image: Python 3.12 slim for minimal size
FROM python:3.12-slim-bookworm AS base

# Metadata
LABEL maintainer="CollabIQ Team"
LABEL description="CollabIQ - AI-powered email processing and Notion integration"
LABEL version="0.1.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/root/.local/bin:$PATH"

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install UV package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Set working directory
WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (production only, no dev dependencies)
# Using --no-install-project to only install deps first for better caching
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source code
COPY src/ ./src/
COPY README.md ./

# Install the project itself and compile bytecode
RUN uv sync --frozen --no-dev && \
    uv run python -m compileall -q /app/src

# Create directories for runtime data (credentials will be mounted here)
RUN mkdir -p /app/credentials /app/data /app/logs

# Health check command
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD uv run collabiq config validate || exit 1

# Set the entrypoint to the CLI
ENTRYPOINT ["uv", "run", "collabiq"]

# Default command (can be overridden)
CMD ["--help"]
