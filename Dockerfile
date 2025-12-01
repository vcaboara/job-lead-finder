###############
# Builder stage
###############
FROM python:3.11-slim AS builder

ARG INSTALL_TEST_DEPS=false
ARG INSTALL_GEMINI=false
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Build tools for any native wheels (kept only in builder)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create a venv and install all runtime deps into it
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only package metadata first (for better caching)
COPY pyproject.toml /app/

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install dependencies from pyproject.toml (without source code)
# This layer is cached unless pyproject.toml changes
RUN pip install --no-cache-dir '.[web]' \
    && if [ "${INSTALL_TEST_DEPS}" = "true" ]; then pip install --no-cache-dir '.[test]'; fi \
    && if [ "${INSTALL_GEMINI}" = "true" ]; then pip install --no-cache-dir '.[gemini]'; fi

# Copy source code (changes frequently, so this layer rebuilds often)
COPY src/ /app/src/

# Install the package itself in editable mode (no deps, already installed above)
RUN pip install --no-cache-dir --no-deps -e .

###############
# Runtime stage
###############
FROM python:3.11-slim AS runtime

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
