# Problemas conocidos

| Síntoma | Causa | Solución |
|---|---|---|
| `Generic audio read error occurred from librosa.` con audios que no vienen a 48 kHz | `birdnetlib` oculta el error real: falta `resampy` para remuestrear | Instalar `requirements.txt` completo (incluye `resampy`) |
| `RuntimeError: The starlette.testclient module requires the httpx2 package` al correr las pruebas | Las pruebas necesitan `httpx2`, que no está en las dependencias de producción | `pip install -r requirements-dev.txt` |
| El servicio se reinicia por falta de memoria en Render (512 MB) | La identificación por foto carga torch + transformers (~430 MB) | `PHOTO_CLASSIFICATION_ENABLED=false` y no instalar `requirements-photo.txt` |
| `ModuleNotFoundError: tflite_runtime` o carga de TensorFlow completo | `tflite-runtime` no tiene wheels para Python 3.12+ ni Windows | Usar `ai-edge-litert` (ya en `requirements.txt`); `app/classifier.py` lo registra como `tflite_runtime` |
| El health check de Render falla con 405 | Render revisa la salud con `HEAD` | `/health` ya acepta `GET` y `HEAD`; revisar que el Health Check Path sea `/health` |
| La primera clasificación tras un rato sin uso tarda más de un minuto | En el plan gratuito el servicio se duerme y al despertar carga BirdNET | Es esperado: el frontend muestra el calentamiento y espera hasta 3 minutos |
| `/analyze` responde 401 | `AI_ENGINE_API_KEY` del backend no coincide con `INTERNAL_API_KEY` | Poner el mismo valor en ambos servicios |
