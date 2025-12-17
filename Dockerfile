# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app

CMD python manage.py migrate \
    && python manage.py sync_senders \
    && python3 manage.py sync_webhook_handlers \
    && python manage.py collectstatic --no-input \
    && gunicorn atl_asana.wsgi:application --bind 0.0.0.0:8000