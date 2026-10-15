# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

## [0.10.0] — 2026-10-15

### Añadido
- Endpoint `GET /datasets/{id}/cleaned.csv` para descargar el CSV resultante tras aceptar el plan de limpieza.
- La descarga requiere que el plan esté aplicado y respeta el aislamiento por usuario (404 para usuarios ajenos).
- Prueba de contrato `test_download_cleaned_csv` que verifica el flujo completo (antes/después de aceptar y aislamiento).

### Cambiado
- Versión del paquete a 0.10.0.
- Descripción de la API y del paquete actualizadas.

## [0.9.0] — 2026-10-14

### Añadido
- Aislamiento de informes por usuario: la cabecera `X-User-Id` es obligatoria. Cada usuario solo accede a sus propios datasets.
- `DatasetStore` persiste bajo `data/users/{user_id}/datasets/{id}/`.
- Endpoints reales: `POST /datasets`, `GET /datasets/{id}`, `POST /datasets/{id}/accept`, `GET /datasets/{id}/report.html`.
- Pruebas de contrato que verifican aislamiento (usuario ajeno recibe 404) y exigencia de cabecera.

### Cambiado
- Versión del paquete a 0.9.0.
- Descripción del paquete y de la API actualizadas.
- Corrección menor en el renderizado HTML cuando el número de clases es un entero.

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
