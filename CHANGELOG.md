# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

### Añadido
- Registro diario del 2026-11-19 documentando la revisión completa del ROADMAP y la ausencia de ítems pendientes.

### Cambiado
- Nota de estado en ROADMAP confirmando finalización de fases 0-31 y propuesta de siguiente fase.

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

## [0.38.0] — 2026-11-16

### Añadido
- Parámetro opcional `format=parquet` en el endpoint `GET /datasets/{id}/download` para exportar el dataset limpio en formato Parquet.
- Pruebas de API que verifican la respuesta Parquet (content-type y magic number PAR1).

### Cambiado
- Versión del paquete y de la API a 0.38.0.
- ROADMAP: nueva Fase 29 — Descarga del dataset limpio en formato Parquet, marcada como completada.
- Descripciones del paquete, API y README actualizadas.

## [0.37.0] — 2026-11-15

### Añadido
- Inclusión de la inercia del mejor modelo KMeans (`best_inertia`) en el resultado de clustering del asesor de modelos.
- Exposición de la inercia en la sección de evaluación de clustering del informe HTML autocontenido.
- Pruebas unitarias que verifican la presencia y el tipo de `best_inertia` en el asesor y su renderizado en el HTML.

### Cambiado
- Versión del paquete y de la API a 0.37.0.
- ROADMAP: nueva Fase 28 — Exposición de la inercia de clustering, marcada como completada.
- Descripciones del paquete, API y README actualizadas.

## [0.36.0] — 2026-11-14

### Añadido
- Sección dedicada en el informe HTML autocontenido que muestra la distribución de etiquetas de cluster (conteos y porcentajes) cuando están disponibles en el resultado de clustering del asesor persistido.
- Pruebas unitarias que verifican la presencia de la sección de distribución de clusters en el HTML generado.

### Cambiado
- Versión del paquete y de la API a 0.36.0.
- ROADMAP: Fase 27 — Visualización de clusters en informe HTML, marcada como completada.
- Descripción del paquete y README actualizados.

## [0.35.0] — 2026-11-12

### Añadido
- Endpoint `GET /datasets/{id}/download` que retorna el dataset limpio en formato CSV tras la aceptación del plan.
- Parámetro opcional `include_clusters=true` en el endpoint de descarga que añade una columna `cluster` cuando las etiquetas del asesor coinciden en longitud con el dataframe limpio.
- Pruebas de API que verifican el requisito de aceptación previa y la respuesta CSV.

### Cambiado
- Versión del paquete y de la API a 0.35.0.
- ROADMAP: nueva Fase 26 — Descarga del CSV limpio con etiquetas de cluster opcionales, marcada como completada.
- Descripción del paquete y README actualizados.

## [0.34.0] — 2026-11-11

### Añadido
- Inclusión de las etiquetas de cluster (labels) del mejor k en el resultado de clustering del asesor.
- Endpoint `GET /datasets/{id}/clusters` que expone las etiquetas de clustering cuando están disponibles en el asesor persistido.
- Pruebas unitarias y de API que verifican la presencia de etiquetas y el nuevo endpoint.

### Cambiado
- Versión del paquete y de la API a 0.34.0.
- ROADMAP: nueva Fase 25 — Exposición de etiquetas de clustering, marcada como completada.
- Descripción del paquete y README actualizados.

## [0.33.0] — 2026-11-10

### Añadido
- Persistencia del resultado del asesor de modelos en el registro del dataset (`meta.json`) al cargar y al aceptar el plan.
- El endpoint `GET /datasets/{id}/advisor` y la generación del informe HTML reutilizan el asesor persistido, evitando recomputación en consultas repetidas.
- Actualización automática del asesor sobre la vista limpia al aceptar el plan.

### Cambiado
- Versión del paquete y de la API a 0.33.0.
- ROADMAP: nueva Fase 24 — Persistencia del asesor de modelos, marcada como completada.
