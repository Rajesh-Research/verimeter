# Stage 1: Build dependency environment
FROM python:3.13-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.8.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

# Install system dependencies needed for compiling python helpers (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /app

# Copy dependency specifications
COPY pyproject.toml poetry.lock ./

# Install project dependencies
RUN poetry install --no-root --only main

# Stage 2: Runtime image
FROM python:3.13-slim AS runner

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Copy installed virtualenv from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy source library code and dependencies
COPY src/ /app/src/
COPY datasets/ /app/datasets/
COPY empirical/ /app/empirical/
COPY simulation/ /app/simulation/
COPY validation/ /app/validation/
COPY pyproject.toml README.md /app/

# Install the package itself in editable mode without reinstalling dependencies
RUN pip install --no-deps -e .

EXPOSE 8000

# Default command to run FastAPI app
CMD ["uvicorn", "verimeter.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
