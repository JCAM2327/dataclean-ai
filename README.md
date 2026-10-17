# DataClean AI

Herramienta para perfilar datasets tabulares, detectar issues de calidad, generar y aplicar planes de limpieza, detectar variable objetivo y comparar modelos baseline.

## Uso por línea de comandos

```bash
python -m dataclean.cli examples/sample.csv
```

## API

Servidor FastAPI con aislamiento de informes por usuario y documentación OpenAPI enriquecida (disponible en `/docs` y `/openapi.json`).

- Cabecera obligatoria: `X-User-Id`
- Cabecera opcional: `X-API-Key` (exigida solo si se configura `DATACLEAN_API_KEY`)
- `POST /datasets` — carga CSV y genera informe
- `GET /datasets/{id}` — consulta el registro
- `POST /datasets/{id}/accept` — aplica el plan de limpieza
- `GET /datasets/{id}/report.html` — informe HTML autocontenido
- `GET /datasets/{id}/cleaned.csv` — descarga del CSV limpio (tras aceptar el plan)

```bash
uvicorn dataclean.api:app --reload
```

Versión actual: 0.12.0
