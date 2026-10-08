# DataClean AI

Plataforma para automatizar la limpieza, validación y análisis de datos tabulares. Detecta problemas de calidad, recomienda mejoras y, cuando el dataset lo permite, prepara la comparación de modelos de machine learning.

**Estado actual:** fase 2 cerrada — comparación de baselines y modelos simples.  
**Última actualización documentada:** 2026-10-08.

## Flujo del producto

```text
CSV
  → perfil (filas, tipos, nulos, únicos, duplicados, estadísticas numéricas)
  → issues (nulos altos, constantes, identificadores, outliers IQR, duplicados)
  → plan explícito (columna, acción, justificación)
  → CSV limpio + delta de calidad
  → objetivo numérico (regresión) o categórico (clasificación)
  → comparación de modelos si existe variable objetivo
  → API e interfaz de revisión del plan   ← siguiente
```

## Uso rápido

```bash
pip install -r requirements.txt
python -m dataclean.cli examples/sample.csv
python -m dataclean.cli examples/sample.csv --target objetivo --apply --cleaned /tmp/limpio.csv --out /tmp/informe.json
pytest
```

## Documentación de avance

| Documento | Contenido |
|-----------|-----------|
| [CHANGELOG.md](CHANGELOG.md) | Historial versionado de cambios |
| [ROADMAP.md](ROADMAP.md) | Fases y pendientes |
| [docs/diario/](docs/diario/) | Registro diario de trabajo (formato profesional) |

## Estructura del repositorio

```text
dataclean/          # Núcleo de perfil, calidad, plan, objetivo y modelos
examples/           # Datos de ejemplo
tests/              # Pruebas unitarias
docs/diario/        # Bitácora diaria de desarrollo
```
