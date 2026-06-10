FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    HF_HOME=/opt/hf-cache

WORKDIR /app

# torch CPU primero: la build por defecto de PyPI arrastra CUDA (~5 GB inútiles sin GPU)
COPY requirements.txt .
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt

# Chromium + librerías de sistema para Playwright (Infojobs/Indeed/LinkedIn renderizan con JS)
RUN playwright install --with-deps chromium \
    && chmod -R a+rX /ms-playwright

# Pre-descarga el modelo de embeddings: el primer arranque no paga los ~90 MB
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .

# Usuario sin privilegios; data/ es el volumen donde escribe offers.json
RUN useradd -m app \
    && mkdir -p /app/data \
    && chown -R app:app /app /opt/hf-cache
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
