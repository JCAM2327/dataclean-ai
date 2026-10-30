# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

## [0.21.0] — 2026-10-30

### Añadido
- Parámetro opcional `drop_high_correlation_threshold` en `build_cleaning_plan`, `analyze_frame`, CLI (`--drop-high-correlation-threshold`) y endpoint `POST /datasets`.
- Cuando se especifica un umbral positivo menor a 1, se identifican pares de columnas numéricas restantes cuya correlación absoluta de Pearson es superior o igual al umbral; se excluye una de ellas (preferencia por mayor tasa de faltantes, luego menor desvío estándar, luego nombre) mediante una acción `drop_column` con razón `high_correlation`.
- El paso registra la columna correlacionada, el valor de correlación y el umbral en los parámetros.
- Prueba unitaria `test_drop_high_correlation_threshold`.

### Cambiado
- Versión del paquete y de la API a 0.21.0.
- Descripción del paquete, README y esquema OpenAPI actualizados.
- ROADMAP: nueva Fase 11 — Selección de características por correlación, con el ítem de exclusión por alta correlación marcado como completado.

## [0.20.0] — 2026-10-26

### Añadido
- Parámetro opcional `drop_low_variance_threshold` en `build_cleaning_plan`, `analyze_frame`, CLI (`--drop-low-variance-threshold`) y endpoint `POST /datasets`.
- Cuando se especifica un umbral positivo, las columnas numéricas cuyo desvío estándar observado (población, sobre valores no nulos) es inferior al umbral se excluyen del plan mediante una acción `drop_column` con razón `low_variance`.
- El paso registra el desvío calculado y el umbral en los parámetros.
- Prueba unitaria `test_drop_low_variance_threshold`.

### Cambiado
- Versión del paquete y de la API a 0.20.0.
- Descripción del paquete, README y esquema OpenAPI actualizados.
- ROADMAP: nueva Fase 10 — Selección de características básica, con el ítem de exclusión por baja varianza marcado como completado.

## [0.19.0] — 2026-10-24

### Añadido
- Parámetro opcional `onehot_drop_first` en `build_cleaning_plan`, `analyze_frame` y CLI (`--onehot-drop-first`).
- Cuando es verdadero y `encode_categorical="onehot"`, se omite la primera categoría ordenada como referencia (drop_first) para evitar multicolinealidad perfecta.
- El paso de plan registra `drop_first` y `dropped_category` en los parámetros.
- Parámetro de consulta `onehot_drop_first` en `POST /datasets`.
- Prueba unitaria `test_onehot_drop_first`.

### Cambiado
- Versión del paquete y de la API a 0.19.0.
- Descripción del paquete, README y esquema OpenAPI actualizados.
- ROADMAP: nueva Fase 9 — Refinamientos de codificación, con el ítem de drop_first marcado como completado.
