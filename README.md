# DataClean AI

Plataforma para perfilar datasets tabulares, detectar problemas de calidad, generar y aplicar planes de limpieza, detectar variable objetivo, comparar modelos baseline e informar importancia de variables. Incluye asesor de estrategias de modelado con evaluación de clustering (KMeans) y estabilidad bootstrap configurable con intervalos de confianza para métricas de clustering.

## Instalación

```bash
pip install -r requirements.txt
```

## Uso básico de la CLI

```bash
python -m dataclean.cli examples/sample.csv --bootstrap-resamples 30
```

Consulte [docs/cli-examples.md](docs/cli-examples.md) para ejemplos adicionales (aplicación del plan, preprocesamiento, exportación).

## API

La API FastAPI expone endpoints documentados en OpenAPI:

- `GET /health` — estado del servicio
- `POST /datasets` — carga y análisis de un dataset
- `GET /datasets/{id}` — recuperación del informe
- `GET /datasets/{id}/report.html` — informe HTML

Inicie con:

```bash
uvicorn dataclean.api:app --reload
```

La documentación interactiva está disponible en `/docs`.

## Versión

0.48.0
