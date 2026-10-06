# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

### Planeado
- Comparación de baselines (mayoría / media) frente a dos modelos simples.
- Informe de métricas de modelado y advertencias asociadas al ajuste.

## [0.3.0] — 2026-10-06

### Añadido
- Detección de variable objetivo (`dataclean.target.detect_target`): distingue objetivo numérico (regresión) y categórico (clasificación).
- Inferencia por alias de nombre (`objetivo`, `target`, `label`, `y`, `clase`, entre otros) y por cardinalidad; `--target` fija la columna y tiene prioridad.
- Exclusión de identificadores y constantes en la inferencia. El informe declara confianza, candidatos, clases y advertencias de muestra pequeña, desbalance o nulos elevados.
- CLI: el informe JSON incluye `target`; el resumen marca `ready_for_modeling` solo si hay objetivo utilizable.
- Pruebas de inferencia, objetivo explícito, columna inexistente y advertencias.

## [0.2.0] — 2026-10-05

### Añadido
- Plan de limpieza explícito (`dataclean.plan.build_cleaning_plan`): cada paso declara columna, acción y justificación.
- Reglas del plan: eliminar duplicados exactos, excluir constantes e identificadores, descartar columnas con 40% o más de nulos, imputar mediana o moda e incorporar indicador de faltante.
- Aplicación del plan (`apply_plan`) y delta de calidad (`quality_delta`) entre el dataset original y el limpio.
- CLI: el informe JSON incluye el plan; `--apply` y `--cleaned` exportan el CSV limpio y el informe de diferencias.
- Pruebas de construcción y aplicación del plan.

## [0.1.0] — 2026-10-04

### Añadido
- Módulo de perfilado de columnas (`dataclean.profile`): filas, tipos, nulos, valores únicos, duplicados y estadísticas numéricas.
- Detección de issues de calidad (`dataclean.quality`) con severidad y recomendación: nulos elevados, columnas constantes, posibles identificadores, outliers por IQR y filas duplicadas.
- Interfaz de línea de comandos (`python -m dataclean.cli`) para analizar un CSV y emitir informe JSON.
- Dataset de ejemplo (`examples/sample.csv`) y prueba unitaria mínima.
- Documentación inicial: README, ROADMAP y estructura de registro diario en `docs/diario/`.
