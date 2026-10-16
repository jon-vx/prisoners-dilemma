FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app

RUN pip install --no-cache-dir .

COPY alembic.ini ./
COPY alembic ./alembic


FROM base AS test

RUN pip install --no-cache-dir '.[test]'

COPY tests ./tests

CMD ["python", "-m", "pytest", "-ra"]


FROM base AS runtime

RUN useradd --create-home --uid 10001 app

USER app

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
