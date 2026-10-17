# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

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
