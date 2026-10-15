# AlaSonora · Motor de IA

Microservicio bioacústico de AlaSonora: FastAPI + BirdNET (a través de `birdnetlib`). Identifica
aves a partir de grabaciones de audio y, de forma opcional, a partir de fotos. Solo lo llama el
backend de Spring Boot, autenticado con una clave interna; el navegador nunca habla con él.

## Instalación

Requiere Python 3.12.3 (la versión de `.python-version`).

```bash
python -m venv .venv
.venv/Scripts/activate       # Windows
source .venv/bin/activate    # Linux / macOS
pip install -r requirements.txt
cp .env.example .env         # define INTERNAL_API_KEY
```

Para usar también la identificación por foto: `pip install -r requirements.txt -r requirements-photo.txt`.

## Ejecución

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`AI_ENGINE_API_KEY` en el `.env` del backend debe ser igual a `INTERNAL_API_KEY` de este servicio.

## Pruebas

Las pruebas son autoverificaciones con `assert` (sin pytest) en `app/test_*.py`. Ninguna carga el
modelo BirdNET: usan señales sintéticas o un clasificador falso.

```bash
pip install -r requirements-dev.txt   # agrega httpx2, que necesita el TestClient
cp .env.example .env                  # basta con el valor de ejemplo de INTERNAL_API_KEY
python -m app.run_tests               # corre todas y falla si alguna falla
python -m app.test_audio_quality      # o una sola
```

El workflow `.github/workflows/ci.yml` corre lo mismo en cada push a `main`.

## Dependencias

- `requirements.txt`: todo lo que necesita la ruta de audio (`/analyze`).
- `requirements-photo.txt`: torch, torchvision, transformers y pillow, que **solo** usa
  `/classify-photo`. Instálalo únicamente si la identificación por foto está activa
  (`PHOTO_CLASSIFICATION_ENABLED=true`, el valor por defecto). Con la bandera en `false` estas
  librerías nunca se importan y el despliegue puede omitirlas; activarla sin instalarlas hace fallar
  `/classify-photo`.

## Render (Web Service de Python nativo, sin Docker)

| Ajuste | Valor |
|---|---|
| Root Directory | `ai-engine` |
| Build Command | `pip install -r requirements.txt` (solo audio; agrega `-r requirements-photo.txt` si se reactivan las fotos) |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |

Variables de entorno:

- `INTERNAL_API_KEY` (obligatoria, el mismo valor que `AI_ENGINE_API_KEY` del backend).
- `PHOTO_CLASSIFICATION_ENABLED=false` en instancias de 512 MB: solo cabe la ruta de audio
  (~360 MB en uso); servir fotos lleva el proceso a ~750 MB, así que `/classify-photo` responde 503
  en lugar de cargar el modelo.
- Python sale de `.python-version` (3.12.3, la versión validada); si Render lo ignora, define
  `PYTHON_VERSION=3.12.3`.

## Pipeline de audio

Cada audio se limpia (`AudioPreprocessor`: filtro pasa-altos + normalización de pico) y pasa un
control de calidad (`AudioQualityAnalyzer`: rechaza el ruido de fondo excesivo o la ausencia de
frecuencias típicas de aves) antes de llegar a BirdNET; ver `app/audio_preprocessing.py` y
`app/audio_quality.py`. Los umbrales se ajustan con variables de entorno
(`AUDIO_HIGHPASS_CUTOFF_HZ`, `AUDIO_NOISE_FLATNESS_THRESHOLD`,
`AUDIO_BIRD_BAND_ENERGY_RATIO_THRESHOLD`).
