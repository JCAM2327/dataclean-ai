# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

## [0.14.0] — 2026-10-19

### Añadido
- Soporte de carga de formatos adicionales: Excel (`.xlsx`, `.xls`) y Parquet, tanto en CLI como en la API.
- Módulo `dataclean.io` con `load_dataframe` que detecta el formato por extensión (ruta o bytes).
- Constante `SUPPORTED_EXTENSIONS` exportada para validación.
- Pruebas unitarias `tests/test_io.py` y pruebas de contrato de API para Excel, Parquet y formato no soportado.

### Cambiado
- Versión del paquete y de la API a 0.14.0.
- Descripción del paquete, README y esquema OpenAPI actualizados para reflejar los formatos soportados.
- Endpoint `POST /datasets` acepta CSV, Excel y Parquet; el resumen OpenAPI pasa a "Cargar dataset tabular".

## [0.13.0] — 2026-10-18

### Añadido
- Acción de plan `clip_outliers`: para columnas numéricas con outliers por criterio IQR (1.5·IQR y fracción ≥ 1 %), se calculan límites a partir de los datos observados y se recortan los valores fuera de rango.
- Parámetros del paso: `lower`, `upper` y `count`.
- Prueba unitaria `test_clip_outliers_iqr` que verifica generación del paso y aplicación correcta de los límites.

### Cambiado
- Versión del paquete a 0.13.0.
- Descripción del paquete actualizada para incluir el clipping de outliers.

## [0.12.0] — 2026-10-17

### Añadido
- Autenticación opcional por API key: si se define la variable de entorno `DATACLEAN_API_KEY`, todos los endpoints exigen la cabecera `X-API-Key` con el valor coincidente.
- La cabecera `X-User-Id` sigue siendo obligatoria para el aislamiento de informes.
- Pruebas de contrato `test_optional_api_key_enforced_when_configured` y `test_api_key_ignored_when_not_configured`.

### Cambiado
- Versión del paquete y de la API a 0.12.0.
- Descripción del paquete y de la API actualizadas para incluir la autenticación opcional.

## [0.11.0] — 2026-10-16

### Añadido
- Documentación OpenAPI enriquecida: etiquetas (`Datasets`, `Informes`), resúmenes, descripciones detalladas y modelos de respuesta Pydantic (`UploadResponse`, `AcceptResponse`, `Summary`) en todos los endpoints.
- Esquema OpenAPI personalizado con logo y descripción ampliada de la plataforma.
- Prueba de contrato `test_openapi_enriched` que verifica versión, descripciones, tags y modelos en `/openapi.json`.

### Cambiado
- Versión del paquete y de la API a 0.11.0.
- Descripción del paquete actualizada para incluir la documentación OpenAPI.
