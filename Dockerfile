# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim

# Note: .dockerignore is symlinked to .gitignore for unified exclusion rules

# Set working directory
WORKDIR /app

# Install uv for faster dependency management
# https://github.com/astral-sh/uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# Copy dependency files and README first for better layer caching
COPY pyproject.toml README.md ./

# Copy the application source code (needed for editable install)
COPY src/ ./src/

# Install dependencies using uv
RUN uv pip install -e .

# Copy test files (optional, for testing in container)
COPY tests/ ./tests/
COPY pytest.ini ./

# Create directory for Garmin tokens
RUN mkdir -p /root/.garminconnect && \
    chmod 700 /root/.garminconnect

# Add transport/port/host env vars (default to stdio and 8000)
ENV GARMIN_MCP_TRANSPORT=stdio \
    GARMIN_MCP_PORT=8000 \
    GARMIN_MCP_HOST=127.0.0.1 \
    GARMIN_USE_UV=false

# Copy entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose the application (if needed for network communication)
# Note: MCP servers typically communicate via stdio, so no port exposure is usually needed
EXPOSE 8000

# Set the entrypoint to run the MCP server via wrapper (handles GARMIN_MCP_TRANSPORT)
ENTRYPOINT ["/app/entrypoint.sh"]

# Health check (optional - adjust based on your needs)
# HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
#   CMD python -c "import sys; sys.exit(0)"
