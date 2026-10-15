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
