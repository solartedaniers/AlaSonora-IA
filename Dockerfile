# Imagen opcional del motor: Render lo despliega como servicio Python nativo, sin Docker.
FROM python:3.12.3-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app app
# Genero la caché de Matplotlib dentro de la imagen, igual que el build de Render.
RUN python -m app.prepare_runtime

# INTERNAL_API_KEY y el resto de la configuración llegan como variables de entorno al correr.
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
