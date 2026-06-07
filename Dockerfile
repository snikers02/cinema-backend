FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.lock .
RUN pip install --no-cache-dir --only-binary :all: -r requirements.lock

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
