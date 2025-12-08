###############
# Builder stage
###############
FROM python:3.12-slim AS builder

ARG INSTALL_TEST_DEPS=false
ARG INSTALL_GEMINI=false
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy only package metadata first (for better caching)
COPY pyproject.toml /app/

# Create virtual environment and install dependencies
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install --no-cache '.[web]' && \
    if [ "${INSTALL_TEST_DEPS}" = "true" ]; then uv pip install --no-cache '.[test]'; fi && \
    if [ "${INSTALL_GEMINI}" = "true" ]; then uv pip install --no-cache '.[gemini]'; fi

# Copy source code (changes frequently, so this layer rebuilds often)
COPY src/ /app/src/

# Install the package itself in editable mode (no deps, already installed above)
RUN . /opt/venv/bin/activate && uv pip install --no-deps -e .

###############
# Runtime stage
###############
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only the pre-built virtualenv with installed deps and our package
COPY --from=builder /opt/venv /opt/venv
# Copy the source code from builder (needed for editable install)
COPY --from=builder /app/src /app/src
COPY --from=builder /app/pyproject.toml /app/pyproject.toml

ENV PATH="/opt/venv/bin:$PATH"

# Default command is a lightweight health probe; compose overrides for UI
CMD ["python", "-m", "app.main", "health"]
