# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

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
