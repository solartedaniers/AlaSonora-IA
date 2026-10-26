# API del motor de IA

Servicio interno: solo lo llama el backend de AlaSonora. FastAPI publica además la especificación
OpenAPI interactiva en `/docs`.

## Autenticación

Todas las rutas, salvo `/health`, exigen la cabecera `X-Internal-Api-Key` con el valor de
`INTERNAL_API_KEY`.

| Caso | Respuesta |
|---|---|
| Falta la cabecera | `401 {"detail": "Not authenticated"}` |
| Clave incorrecta | `401 {"detail": "Invalid API key"}` |

## `GET /health` · `HEAD /health`

Sin autenticación. No carga nada: el modelo ya se cargó al arrancar. Render la usa como health
check (con `HEAD`) y el backend para saber si el motor ya despertó.

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

## `POST /analyze`

Clasifica una grabación con BirdNET. Cuerpo `multipart/form-data`:

| Campo | Tipo | Obligatorio | Por defecto |
|---|---|---|---|
| `audio` | archivo de audio (el backend solo envía wav, flac o mp3) | sí | — |
| `min_confidence` | número 0–1 | no | `DEFAULT_MIN_CONFIDENCE` |
| `max_results` | entero | no | `DEFAULT_MAX_RESULTS` |
| `recorded_at` | fecha ISO 8601 | no | — |
| `latitude`, `longitude` | número | no | — (solo con GPS real; si llegan, BirdNET filtra por especies esperables en esa zona) |

Antes de BirdNET el audio se limpia y pasa el control de calidad. Las especies se deduplican (mejor
confianza por especie) y se descartan las clases de no-evento (voz humana, ruido, sirenas…).

```bash
curl -X POST http://localhost:8000/analyze \
  -H "X-Internal-Api-Key: $INTERNAL_API_KEY" \
  -F audio=@grabacion.wav -F min_confidence=0.25
# {"candidates":[{"scientific_name":"Bubo virginianus","common_name":"Great Horned Owl","confidence":0.7}]}
```

Una lista vacía significa que ninguna especie superó el umbral.

## `POST /classify-photo`

Identifica un ave en una foto con un modelo EfficientNetB2 de Hugging Face (`PHOTO_MODEL_ID`),
independiente de BirdNET. El modelo se carga la primera vez que se usa, no al arrancar. Cuerpo
`multipart/form-data`:

| Campo | Tipo | Obligatorio | Por defecto |
|---|---|---|---|
| `photo` | archivo de imagen | sí | — |
| `min_confidence` | número 0–1 | no | `DEFAULT_PHOTO_MIN_CONFIDENCE` |
| `max_results` | entero | no | `DEFAULT_PHOTO_MAX_RESULTS` |

```bash
curl -X POST http://localhost:8000/classify-photo \
  -H "X-Internal-Api-Key: $INTERNAL_API_KEY" \
  -F photo=@ave.jpg
# {"candidates":[{"label":"Azure Jay","confidence":0.91}]}
```

Con `PHOTO_CLASSIFICATION_ENABLED=false` responde 503 sin importar torch ni transformers.

## Errores

Los errores propios del motor responden `{"code": "<CÓDIGO>", "detail": "<texto corto en inglés>"}`. El
`code` es estable: el backend lo traduce a su `ApiErrorCode` y el frontend muestra el texto en español o
inglés. El `detail` queda para leer en logs y para backends anteriores que solo leían ese campo.

| Status | Ruta | Cuándo | `code` |
|---|---|---|---|
| 401 | `/analyze`, `/classify-photo` | Falta la clave o es incorrecta | — (`detail`: `Not authenticated` / `Invalid API key`) |
| 413 | `/analyze`, `/classify-photo` | El archivo pasa `MAX_AUDIO_BYTES` o `MAX_PHOTO_BYTES`; dejo de leerlo apenas lo supera | `AUDIO_TOO_LARGE` / `PHOTO_TOO_LARGE` |
| 415 | `/analyze`, `/classify-photo` | La firma del archivo no es WAV, FLAC o MP3 (audio) ni JPEG, PNG o WebP (foto) | `AUDIO_UNSUPPORTED` / `PHOTO_UNSUPPORTED` |
| 422 | `/analyze` | Demasiado ruido de fondo | `TOO_NOISY` |
| 422 | `/analyze` | Silencio o sin energía en la banda de aves | `NO_BIRD_SIGNAL` |
| 422 | `/classify-photo` | Ninguna predicción alcanza `min_confidence` | `NO_BIRD_IN_PHOTO` |
| 422 | ambas | Falta el archivo o un campo no es válido | — (lista de errores de validación de FastAPI) |
| 503 | `/classify-photo` | `PHOTO_CLASSIFICATION_ENABLED=false` | `PHOTO_DISABLED` |
