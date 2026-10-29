# DataClean AI

Herramienta para perfilar datasets tabulares, detectar issues de calidad, generar y aplicar planes de limpieza (incluye clipping de outliers IQR, estrategias de imputación configurables, estandarización opcional de columnas numéricas y codificación opcional de variables categóricas con soporte drop_first y exclusión opcional de columnas numéricas de baja varianza), detectar variable objetivo y comparar modelos baseline.

Soporta carga de CSV, Excel (.xlsx/.xls) y Parquet.

## Uso por línea de comandos

```bash
python -m dataclean.cli examples/sample.csv
python -m dataclean.cli datos.xlsx
python -m dataclean.cli datos.parquet
```

## API

Servidor FastAPI con aislamiento de informes por usuario y documentación OpenAPI enriquecida (disponible en `/docs` y `/openapi.json`).

- Cabecera obligatoria: `X-User-Id`
- Cabecera opcional: `X-API-Key` (exigida solo si se configura `DATACLEAN_API_KEY`)
- Parámetro opcional: `scale_numeric=true` en `POST /datasets` para activar estandarización z-score
- Parámetro opcional: `encode_categorical=onehot|ordinal` en `POST /datasets` para codificación categórica
- Parámetro opcional: `onehot_drop_first=true` en `POST /datasets` para omitir la categoría de referencia en one-hot
- Parámetro opcional: `drop_low_variance_threshold=<float>` en `POST /datasets` para excluir columnas numéricas con desvío estándar observado inferior al umbral
- `POST /datasets` — carga CSV, Excel o Parquet y genera informe
- `GET /datasets/{id}` — consulta el registro
- `POST /datasets/{id}/accept` — aplica el plan de limpieza
- `GET /datasets/{id}/report.html` — informe HTML autocontenido
- `GET /datasets/{id}/cleaned.csv` — descarga del CSV limpio (tras aceptar el plan)

```bash
uvicorn dataclean.api:app --reload
```

Versión actual: 0.20.0
