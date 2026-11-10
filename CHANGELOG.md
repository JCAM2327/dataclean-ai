# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

## [0.33.0] — 2026-11-10

### Añadido
- Persistencia del resultado del asesor de modelos en el registro del dataset (`meta.json`) al cargar y al aceptar el plan.
- El endpoint `GET /datasets/{id}/advisor` y la generación del informe HTML reutilizan el asesor persistido, evitando recomputación en consultas repetidas.
- Actualización automática del asesor sobre la vista limpia al aceptar el plan.

### Cambiado
- Versión del paquete y de la API a 0.33.0.
- ROADMAP: nueva Fase 24 — Persistencia del asesor de modelos, marcada como completada.

## [0.32.0] — 2026-11-09

### Añadido
- Endpoint `GET /datasets/{id}/advisor` que expone las recomendaciones de `suggest_modeling_strategy`.
- Evaluación mínima de clustering mediante KMeans y score de silueta cuando el clustering es viable (al menos 2 columnas numéricas y 20 filas).
- Inclusión de la sección de asesor (estrategia, recomendaciones y resultados de clustering) en el informe HTML autocontenido.
- Pruebas de API que verifican el endpoint de asesor.

### Cambiado
- `suggest_modeling_strategy` ahora incluye opcionalmente `clustering_results` con mejor k y siluetas.
- Versión del paquete y de la API a 0.32.0.
- Descripción del paquete, README y esquema OpenAPI actualizados.
- ROADMAP: nueva Fase 23 — Exposición del asesor de modelos, marcada como completada.

## [0.31.0] — 2026-11-07

### Añadido
- Módulo `dataclean/advisor.py` con la función `suggest_modeling_strategy`.
- Recomendaciones de estrategia de modelado (supervisada, no supervisada o insuficiente) basadas en la presencia de variable objetivo, estado del informe de modelos, número de columnas numéricas utilizables y tamaño de muestra.
- Detección de viabilidad de clustering (al menos dos columnas numéricas con variación y 20 o más filas).
- Pruebas unitarias en `tests/test_advisor.py`.

### Cambiado
- Versión del paquete a 0.31.0.
- ROADMAP: nueva Fase 22 — Asesor de modelos y análisis no supervisado, marcada como completada.
