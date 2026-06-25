FROM python:3.11-slim

# Instalar dependencias del sistema para Whisper (ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements primero para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente y el modelo entrenado
COPY . .

# Puerto de la API
EXPOSE 8000

# Comando para levantar la API con Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
