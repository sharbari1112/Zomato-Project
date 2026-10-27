FROM python:3.12-slim

WORKDIR /app

COPY requirements.prod.txt .
RUN pip install --no-cache-dir -r requirements.prod.txt

COPY app ./app
# data/catalog.parquet is gitignored — must exist in the Docker build context.
COPY data/catalog.parquet ./data/catalog.parquet

ENV CATALOG_PATH=data/catalog.parquet
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV SERVE_UI=false

# Render injects PORT; default 8000 for local `docker run`.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
