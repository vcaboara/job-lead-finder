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

# Copy package metadata and source
COPY pyproject.toml /app/
COPY src/ /app/src/

RUN pip install --upgrade pip setuptools wheel

# Install our package and runtime deps into the venv
RUN pip install --no-cache-dir . \
    && pip install --no-cache-dir fastapi uvicorn[standard] httpx python-multipart \
    && if [ "${INSTALL_TEST_DEPS}" = "true" ]; then pip install --no-cache-dir pytest pytest-cov; fi \
    && if [ "${INSTALL_GEMINI}" = "true" ]; then pip install --no-cache-dir google-genai google-generativeai; fi

###############
# Runtime stage
###############
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only the pre-built virtualenv with installed deps and our package
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Default command is a lightweight health probe; compose overrides for UI
CMD ["python", "-m", "app.main", "health"]
