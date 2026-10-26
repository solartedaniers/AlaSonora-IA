# Imagen del motor: es la que Render construye y corre en producción.
FROM python:3.12.3-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app app
# Genero la caché de Matplotlib en el build: así el arranque en frío no la construye.
RUN python -m app.prepare_runtime

# INTERNAL_API_KEY y el resto de la configuración llegan como variables de entorno al correr.
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
