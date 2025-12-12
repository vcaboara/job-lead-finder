# AI Coder - Autonomous Development Container
# Optimized with uv for 10-100x faster pip installs
FROM python:3.12-slim as base

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

# Install system dependencies in single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Install Aider (AI pair programming tool)
RUN uv pip install --system aider-chat

# Set working directory
WORKDIR /workspace

# Copy task processor
COPY task_processor.py /usr/local/bin/task_processor.py
RUN chmod +x /usr/local/bin/task_processor.py

# Configure git for commits
RUN git config --global user.name "AI Coder" && \
    git config --global user.email "ai-coder@localhost"

# Run task processor
CMD ["python", "/usr/local/bin/task_processor.py"]
