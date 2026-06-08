FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app app

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# requirements.lock — pinned versions (pip-compile)
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

COPY apps/ ./apps/
COPY core/ ./core/
COPY plugins/ ./plugins/
COPY manage.py .

RUN mkdir -p /app/media && chown -R app:app /app

USER app

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
