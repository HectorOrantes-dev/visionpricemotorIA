FROM python:3.11-slim

# Instalar dependencias del sistema para Whisper (ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Actualizar pip y setuptools (necesario para compilar openai-whisper)
RUN pip install --upgrade pip setuptools wheel

# Copiar requirements primero para aprovechar la caché de Docker
COPY requirements.txt .

# Instalar openai-whisper primero sin build isolation (necesita pkg_resources)
RUN pip install --no-cache-dir --no-build-isolation openai-whisper==20240930

# Instalar el resto de dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente y el modelo entrenado
COPY . .

# Puerto de la API
EXPOSE 8000

# Comando para levantar la API con Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
