# DataClean AI

Herramienta para perfilar datasets tabulares, detectar issues de calidad, generar y aplicar planes de limpieza (incluye clipping de outliers IQR, estrategias de imputación configurables, estandarización opcional de columnas numéricas, codificación opcional de variables categóricas con soporte drop_first, exclusión opcional de columnas numéricas de baja varianza y exclusión opcional de columnas numéricas altamente correlacionadas), detectar variable objetivo, comparar modelos baseline e informar importancia de variables (con candidatos a exclusión por umbral de importancia opcional, agregación de máximo/media entre modelos y visualización de barras en el informe HTML).

Soporta carga de CSV, Excel (.xlsx/.xls) y Parquet.

## Uso por línea de comandos

```bash
python -m dataclean.cli examples/sample.csv
python -m dataclean.cli datos.xlsx
python -m dataclean.cli datos.parquet
```

## API

Servidor FastAPI con aislamiento de informes por usuario y documentación OpenAPI enriquecida (disponible en `/docs` y `/openapi.json`).

- Cabecera obligatoria: `X-User-Id` (identificador anónimo de sesión generado por el cliente)
- Cabecera opcional: `X-API-Key` (exigida solo si se configura `DATACLEAN_API_KEY`)
- Parámetro opcional: `target=<columna>` en `POST /datasets` para fijar la variable objetivo
- Parámetro opcional: `scale_numeric=true` en `POST /datasets` para activar estandarización z-score
- Parámetro opcional: `encode_categorical=onehot|ordinal` en `POST /datasets` para codificación categórica
- Parámetro opcional: `onehot_drop_first=true` en `POST /datasets` para omitir la categoría de referencia en one-hot
- Parámetro opcional: `drop_low_variance_threshold=<float>` en `POST /datasets` para excluir columnas numéricas con desvío estándar observado inferior al umbral
- Parámetro opcional: `drop_high_correlation_threshold=<float>` en `POST /datasets` para excluir columnas numéricas con |correlación| absoluta superior o igual al umbral
- Parámetro opcional: `importance_threshold=<float>` en `POST /datasets` para reportar candidatos a exclusión por baja importancia de variables
- Parámetro opcional: `drop_low_importance=true` en `POST /datasets` para incluir automáticamente en el plan las columnas de baja importancia (requiere umbral)
- `GET /health` — estado y versión del servicio
- `POST /datasets` — carga CSV, Excel o Parquet y genera informe
- `GET /datasets` — lista los datasets del usuario
- `GET /datasets/{id}` — consulta el registro
- `DELETE /datasets/{id}` — elimina el dataset y sus archivos
- `GET /datasets/{id}/preview` — muestra el dataset original o limpio
- `GET /datasets/{id}/eda` — análisis exploratorio (distribuciones, correlaciones, series e insights)
- `GET /datasets/{id}/validation/suggestions` — reglas de validación sugeridas
- `POST /datasets/{id}/validate` — evalúa reglas y calcula el score de calidad
- `POST /datasets/{id}/accept` — aplica el plan de limpieza
- `GET /datasets/{id}/report.html` — informe HTML autocontenido (incluye barras de importancias agregadas y sección de asesor)
- `GET /datasets/{id}/importances` — importancias de variables persistidas de los modelos no baseline (incluye agregación)
- `GET /datasets/{id}/advisor` — recomendaciones del asesor de modelos (incluye evaluación mínima de clustering cuando es viable)
- `GET /datasets/{id}/clusters` — etiquetas de clustering del mejor k cuando están disponibles

### Configuración operativa

- `DATACLEAN_CORS_ORIGINS` — orígenes permitidos separados por coma; por defecto `*`
- `DATACLEAN_MAX_UPLOAD_BYTES` — tamaño máximo de subida; por defecto 50 MB
- `DATACLEAN_MAX_AGE_HOURS` — retención de datasets; por defecto 24 horas
- `DATACLEAN_CLEANUP_INTERVAL_SECONDS` — frecuencia mínima de limpieza; por defecto 3600 segundos

```bash
uvicorn dataclean.api:app --reload
```

Versión actual: 0.34.0
