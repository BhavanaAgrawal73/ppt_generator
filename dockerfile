# Build a tiny image for public deployment
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && adduser --disabled-password --gecos "app" app \
    && mkdir -p /app/backend /app/frontend && chown -R app:app /app
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
USER app
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
