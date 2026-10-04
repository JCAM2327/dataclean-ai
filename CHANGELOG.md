# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

### Planeado
- Plan de limpieza ejecutable (drop de duplicados, imputación, exclusión de identificadores y constantes).
- Exportación de CSV limpio e informe de diferencias de calidad.

## [0.1.0] — 2026-10-04

### Añadido
- Módulo de perfilado de columnas (`dataclean.profile`): filas, tipos, nulos, valores únicos, duplicados y estadísticas numéricas.
- Detección de issues de calidad (`dataclean.quality`) con severidad y recomendación: nulos elevados, columnas constantes, posibles identificadores, outliers por IQR y filas duplicadas.
- Interfaz de línea de comandos (`python -m dataclean.cli`) para analizar un CSV y emitir informe JSON.
- Dataset de ejemplo (`examples/sample.csv`) y prueba unitaria mínima.
- Documentación inicial: README, ROADMAP y estructura de registro diario en `docs/diario/`.
