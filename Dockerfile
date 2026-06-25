FROM python:3.11-slim

# Instalar dependencias del sistema para Whisper (ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Instalar todo en UNA sola capa para evitar caché de Docker:
# 1. Forzar setuptools 75 (último con pkg_resources)
# 2. Instalar whisper sin build isolation
# 3. Instalar el resto de dependencias
RUN pip install --upgrade pip && \
    pip install "setuptools==75.8.2" wheel && \
    pip install --no-cache-dir --no-build-isolation openai-whisper==20240930 && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente y el modelo entrenado
COPY . .

# Puerto de la API
EXPOSE 8000

# Comando para levantar la API con Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
