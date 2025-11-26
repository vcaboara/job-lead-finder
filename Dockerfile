FROM python:3.11-slim

ARG INSTALL_TEST_DEPS=false
ARG INSTALL_GEMINI=false
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy package metadata and source
COPY pyproject.toml /app/
COPY src/ /app/src/
COPY tests/ /app/tests/

RUN pip install --upgrade pip setuptools

# Install package; optionally install test deps when building for CI
RUN pip install --no-cache-dir . \
    && pip install --no-cache-dir fastapi uvicorn[standard] \
    && if [ "${INSTALL_TEST_DEPS}" = "true" ]; then pip install --no-cache-dir pytest; fi \
    && if [ "${INSTALL_GEMINI}" = "true" ]; then pip install --no-cache-dir google-genai; fi

CMD ["python", "-m", "app.main", "health"]
