FROM node:24-slim AS frontend
WORKDIR /frontend
COPY package.json package-lock.json vite.config.js ./
COPY app/ui ./app/ui
RUN npm ci --ignore-scripts && npm run build

FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/Iftimie/takeaway_challenge"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
COPY --from=frontend /frontend/app/ui/dist ./app/ui/dist
RUN pip install --no-cache-dir . \
    && useradd --uid 10001 --create-home appuser

COPY alembic.ini ./
COPY migrations ./migrations

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).close()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
