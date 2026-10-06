FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements-docker.txt ./

RUN python -m pip install --no-cache-dir -r requirements-docker.txt

RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser --create-home appuser \
    && mkdir -p /app/instance \
    && chown appuser:appuser /app/instance

COPY app.py index.html style.css script.js ./
COPY images/ ./images/

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "python -m flask --app app init-db && exec gunicorn --bind 0.0.0.0:8000 --workers 1 --access-logfile - --error-logfile - app:app"]