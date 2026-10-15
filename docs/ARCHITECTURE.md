# Arquitectura del motor de IA

## Pipeline de audio (`/analyze`)

```
audio subido ─► archivo temporal ─► librosa.load (mono, tasa original)
   ─► AudioPreprocessor.clean      pasa-altos Butterworth (sosfiltfilt, sin desfase) + normalización de pico
   ─► AudioQualityAnalyzer          silencio → NoBirdSignal · aplanamiento espectral alto → TooNoisy
                                    · poca energía en 0,4–8 kHz → NoBirdSignal
   ─► WAV temporal limpio ─► BirdNET (birdnetlib.Recording, fragmentos de 3 s)
   ─► rank_candidates               descarta no-eventos, deja la mejor confianza por especie, ordena y corta
```

- `app/classifier.py` (`BirdNetClassifier`) orquesta el pipeline; `rank_candidates` es una función
  pura para poder probarla sin el modelo.
- El análisis es bloqueante (TFLite), así que `main.py` lo despacha a un `ThreadPoolExecutor`
  acotado (`MAX_INFERENCE_WORKERS`) y el event loop de FastAPI nunca se congela.
- Los archivos temporales se borran en `finally`, aunque el audio no pase el control de calidad.
- Latitud y longitud son opcionales: solo con GPS real, porque restringen BirdNET a las especies
  esperables en esa zona.

## Identificación por foto (`/classify-photo`)

- `app/photo_classifier.py` (`BirdPhotoClassifier`) envuelve un modelo de Hugging Face
  (EfficientNetB2 ajustado a 525 especies): softmax, top-k y umbral de confianza. Si ninguna
  predicción alcanza el umbral lanza `NoBirdInPhotoError` (422).
- Es independiente de BirdNET: otro modelo, otra entrada y otras dependencias
  (`requirements-photo.txt`).
- Se importa y carga de forma perezosa la primera vez que se usa, dentro del pool de inferencia;
  un `threading.Lock` evita que dos peticiones simultáneas lo carguen dos veces.
- `PHOTO_CLASSIFICATION_ENABLED=false` corta antes de importar nada y responde 503.

## Memoria y arranque en frío (instancias de 512 MB)

| Decisión | Dónde | Por qué |
|---|---|---|
| LiteRT en lugar de TensorFlow | `app/classifier.py`, `requirements.txt` | Mismo `Interpreter` con ~180 MB menos de RAM; se registra como `tflite_runtime` antes de importar `birdnetlib` |
| BirdNET cargado una sola vez | `lifespan` en `app/main.py` | Cargarlo por petición sería lento y duplicaría memoria |
| Fotos apagables y perezosas | `PHOTO_CLASSIFICATION_ENABLED` | torch + transformers suman ~430 MB; con la bandera en `false` solo cabe el audio (~360 MB) |
| Caché de Matplotlib en el build | `app/prepare_runtime.py`, `app/__init__.py` | `birdnetlib` importa Matplotlib; la caché de fuentes se genera en el build y no en cada arranque |
| `/health` acepta `HEAD` | `app/main.py` | Render revisa la salud con `HEAD`; sin él respondía 405 y el servicio no quedaba sano al despertar |

El motor no tiene tareas programadas ni pings propios: en el plan gratuito de Render se duerme sin
tráfico, y el backend lo despierta bajo demanda consultando `/health` antes de clasificar.
