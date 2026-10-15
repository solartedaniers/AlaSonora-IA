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
