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
