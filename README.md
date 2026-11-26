# DataClean AI

Plataforma para perfilar datasets tabulares, detectar problemas de calidad, generar y aplicar planes de limpieza, detectar variable objetivo, comparar modelos baseline e informar importancia de variables. Incluye asesor de estrategias de modelado con evaluación de clustering (KMeans) y estabilidad bootstrap configurable con intervalos de confianza para métricas de clustering.

## Uso básico de la CLI

```bash
python -m dataclean.cli examples/sample.csv --bootstrap-resamples 30
```

## Versión

0.47.0
