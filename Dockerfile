# -- Build stage --
FROM python:3.11-slim AS build

# Install and configure poetry environment
RUN pip install --no-cache-dir --disable-pip-version-check poetry==1.4.1

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --without dev --no-root --no-interaction --no-ansi --no-cache

# -- Runtime stage --
FROM python:3.11-slim AS runtime

# Copy poetry venv
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=build ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY . .

# BOT_TOKEN env variable will be read from .env when running container
# OR set with 'docker run -e'

CMD ["python", "-m", "main.py"]
