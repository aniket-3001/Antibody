# --- Stage 1: build the frontend ---
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: runtime ---
FROM python:3.11-slim AS runtime
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt ./api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

# Bake the fastembed model into the image so the first real report on a cold
# boot doesn't block the event loop downloading it from HuggingFace Hub — on
# Render's free tier that download was slow/blocking enough to fail health
# checks mid-request and trigger a restart before cognify finished. Pinned to
# a fixed path (not under DATA_DIR) so it's baked in regardless of DATA_DIR
# overrides — api/memory/memory_service.py's os.environ.setdefault() will
# respect this pre-set value instead of pointing fastembed at DATA_DIR/cache.
ENV FASTEMBED_CACHE_PATH=/opt/fastembed_cache
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2')"

COPY api/ ./api/
COPY seed/ ./seed/
COPY --from=frontend /app/frontend/dist ./frontend/dist

ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
