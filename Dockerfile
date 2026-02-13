# Dockerfile para Log Analyzer API
FROM python:3.11-slim

# Metadata
LABEL maintainer="log_analyzer"
LABEL description="Log Analyzer - API REST para análisis de logs con LLM"

# Configurar directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema (si fueran necesarias)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar caché de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY app/ ./app/
COPY src/ ./src/
COPY datasets/ ./datasets/

# Crear directorios para outputs
RUN mkdir -p out/reports out/analysis

# Exponer puerto
EXPOSE 8080

# Variables de entorno por defecto
ENV LLM_PROVIDER=ollama
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434
ENV OLLAMA_MODEL=mistral
ENV CACHE_ENABLED=true
ENV CACHE_TTL_SECONDS=60
ENV REPORT_FORMAT=excel
ENV OUT_DIR=/app/out
ENV LOG_LEVEL=INFO
ENV REQUEST_TIMEOUT_SECONDS=120

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Ejecutar la API
CMD ["python", "app/api.py"]
