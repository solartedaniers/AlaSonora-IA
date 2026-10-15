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
