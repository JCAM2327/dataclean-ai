# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

## [0.43.0] — 2026-11-22

### Añadido
- Evaluación bootstrap (20 remuestreos) de la silueta para el mejor k de KMeans en el asesor de modelos.
- Campos `best_silhouette_bootstrap_mean` y `best_silhouette_bootstrap_std` en el resultado de clustering.
- Visualización de las métricas de estabilidad bootstrap en la sección de clustering del informe HTML.
- Pruebas unitarias que verifican la presencia de las nuevas métricas.
- Registro diario del 2026-11-22.

### Cambiado
- Versión del paquete y de la API a 0.43.0.
- ROADMAP: nueva Fase 34 — Estabilidad de la silueta por bootstrap, marcada como completada.
- Descripciones del paquete, API y README actualizadas para incluir la evaluación bootstrap de silueta.

## [0.42.0] — 2026-11-21

### Añadido
- Parámetro opcional `clip_outliers_iqr_multiplier` en `POST /datasets` y en la CLI para configurar el multiplicador IQR del clipping de outliers (por defecto 1.5; valor <= 0 desactiva el clipping).
- Inclusión del multiplicador en los parámetros de las acciones `clip_outliers` del plan.
- Pruebas unitarias y de API que verifican el comportamiento con multiplicadores personalizados y la desactivación.
- Registro diario del 2026-11-21.

### Cambiado
- Versión del paquete y de la API a 0.42.0.
- ROADMAP: nueva Fase 33 — Configuración de clipping de outliers vía API, marcada como completada.
- Descripciones del paquete, API y README actualizadas para incluir el multiplicador IQR configurable.

## [0.41.0] — 2026-11-20

### Añadido
- Parámetros opcionales `impute_numeric`, `impute_categorical` e `impute_constant_value` en `POST /datasets` para configurar estrategias de imputación (median, mean, mode, constant) por tipo de columna.
- Construcción del diccionario de estrategias y paso a `analyze_frame` para que el plan de limpieza refleje la configuración.
- Pruebas de API que verifican la presencia de acciones de imputación configuradas en el plan generado.
- Registro diario del 2026-11-20.

### Cambiado
- Versión del paquete y de la API a 0.41.0.
- ROADMAP: Fase 32 — Configuración avanzada del plan de limpieza vía API, marcada como completada.
- Descripciones del paquete, API y README actualizadas para incluir las estrategias de imputación configurables.

## [0.40.0] — 2026-11-18

### Añadido
- Inclusión del índice Calinski-Harabasz (`best_calinski_harabasz`) del mejor modelo KMeans en el resultado de clustering del asesor de modelos.
- Visualización de la métrica Calinski-Harabasz en la sección de evaluación de clustering del informe HTML autocontenido.
- Pruebas unitarias que verifican la presencia y el tipo de `best_calinski_harabasz` en el asesor.

### Cambiado
- Versión del paquete y de la API a 0.40.0.
- ROADMAP: nueva Fase 31 — Exposición del índice Calinski-Harabasz en clustering, marcada como completada.
- Descripciones del paquete, API y README actualizadas.

## [0.39.0] — 2026-11-17

### Añadido
- Inclusión del índice Davies-Bouldin (`best_davies_bouldin`) del mejor modelo KMeans en el resultado de clustering del asesor de modelos.
- Visualización de la métrica Davies-Bouldin en la sección de evaluación de clustering del informe HTML autocontenido.
- Pruebas unitarias que verifican la presencia y el tipo de `best_davies_bouldin` en el asesor.

### Cambiado
- Versión del paquete y de la API a 0.39.0.
- ROADMAP: nueva Fase 30 — Exposición del índice Davies-Bouldin en clustering, marcada como completada.
- Descripciones del paquete, API y README actualizadas.
