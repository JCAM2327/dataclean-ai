# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

### Planeado
- Detección de variable objetivo y comparación de baselines frente a dos modelos simples.
- Informe de métricas y advertencias por muestra pequeña o desbalance.

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
