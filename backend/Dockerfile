FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV SOURCEHUNTER_DB_PATH=/app/data/sourcehunter.sqlite3

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir . \
    && python -m playwright install --with-deps chromium \
    && mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
