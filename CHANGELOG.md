# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [0.48.0] - 2026-11-27

### Añadido
- Implementación funcional de la API FastAPI en `dataclean/api.py` con documentación OpenAPI enriquecida (tags, summaries, descriptions, parámetros).
- Endpoints: `GET /health`, `POST /datasets` (carga y análisis), `GET /datasets/{id}`, `GET /datasets/{id}/report.html`.
- Documentación de ejemplos de uso de la CLI en `docs/cli-examples.md`.
- Ampliación del `README.md` con instrucciones de instalación, ejemplos y arranque de la API.
- Pruebas básicas de la API en `tests/test_api.py`.

### Cambiado
- Actualización de la versión a 0.48.0.

## [0.47.0] - 2026-11-26

### Añadido
- Intervalos de confianza bootstrap (percentil 95%) para las métricas de clustering adicionales: inercia, Davies-Bouldin y Calinski-Harabasz, además de la silueta existente.
- Campos en `clustering_results`: medias, desviaciones estándar y límites de IC para cada métrica bootstrap.
- Actualización de la versión a 0.47.0.

### Cambiado
- El texto de recomendación del asesor incluye el IC95% de la silueta cuando está disponible.

## [0.46.0] - 2026-11-25

### Añadido
- Exposición del parámetro `--bootstrap-resamples` en la CLI para configurar el número de remuestreos bootstrap en el asesor de estrategias de modelado.
- Integración del asesor (`suggest_modeling_strategy`) en el flujo de análisis de la CLI, incluyendo los resultados de clustering y recomendaciones en el informe JSON.
- Actualización de la versión a 0.46.0.

### Cambiado
- El informe generado por la CLI ahora incluye la clave `advisor` con la sugerencia de estrategia.

## [0.45.0] - 2026-11-24

### Añadido
- Parámetro de query opcional `bootstrap_resamples` en el endpoint `POST /datasets`.
- Sincronización de versiones y documentación.
