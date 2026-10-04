# DataClean AI

Plataforma para automatizar la limpieza, validación y análisis de datos tabulares.
Detecta problemas de calidad, recomienda mejoras y, cuando el dataset lo permite, deja listo el camino para comparar modelos.

Estado actual: **fase 0 — núcleo de perfil y calidad** (CLI). Repo inicializado el 2026-10-04.

## Flujo

```text
CSV
  → perfil (filas, tipos, nulos, únicos, duplicados, stats numéricas)
  → issues (nulos altos, constantes, ids, outliers IQR, duplicados)
  → recomendaciones
  → (siguiente) plan de limpieza aplicado + informe
  → (siguiente) split y comparación de modelos si hay target
```

## Uso

```bash
pip install -r requirements.txt
python -m dataclean.cli examples/sample.csv
pytest
```

## Pasos

1. Hecho: perfil + detección de issues + CLI.
2. Siguiente: plan de limpieza ejecutable (drop duplicados, imputación, exclusión de ids/constantes) y CSV limpio.
3. Después: API/UI de carga y comparación simple de modelos (baseline vs. un par de clasificadores/regresores).
