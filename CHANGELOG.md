# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

### Planeado
- Autenticación o aislamiento de informes por usuario.

## [0.8.0] — 2026-10-12

### Añadido
- Exportación formal del informe en HTML: `GET /datasets/{id}/report.html` devuelve un documento autocontenido con resumen, issues, plan, objetivo y comparación de modelos.
- Módulo `dataclean.report.render_report_html` que genera el HTML a partir del registro persistido.
- La respuesta de carga incluye `html_url`.
- Prueba de contrato `test_report_html_export` y cobertura del recurso inexistente.

### Cambiado
- Versión del paquete a 0.8.0.
- Descripción de la API actualizada para incluir exportación HTML.

## [0.7.0] — 2026-10-11

### Añadido
- Persistencia de informes: `DatasetStore` almacena cada dataset en `data/datasets/{id}/` (`meta.json`, `original.csv`, `cleaned.csv` opcional).
- El informe completo y el frame original sobreviven al reinicio del proceso.
- Método `update` para persistir cambios tras la aceptación del plan.
- Prueba de round-trip `test_persistence_survives_store_reload`.

### Cambiado
- Versión del paquete a 0.7.0.
- Descripción de la API actualizada para incluir persistencia.
