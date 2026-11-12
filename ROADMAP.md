# Roadmap — DataClean AI

## Fase 0 — Núcleo de perfil y calidad

- [x] Perfil de columnas
- [x] Issues de calidad con severidad y recomendación
- [x] CLI `python -m dataclean.cli archivo.csv`
- [x] Prueba unitaria mínima
- [x] CHANGELOG y registro diario profesional

## Fase 1 — Limpieza aplicada

- [x] Plan explícito (columna, acción, justificación)
- [x] Aplicar plan y exportar CSV + informe de diferencias de calidad
- [x] Reglas: eliminar duplicados, imputar mediana/moda, marcar nulos, excluir identificadores y constantes

## Fase 2 — Modelado condicional

- [x] Detectar variable objetivo numérica o categórica
- [x] Comparar baselines (mayoría / media) frente a dos modelos simples
- [x] Informe de métricas y advertencias (muestra pequeña o desbalance)

## Fase 3 — Producto

- [x] API de carga de datasets
- [x] Interfaz para revisar issues y aceptar el plan de limpieza
- [x] Persistencia de informes

## Fase 4 — Entrega y acceso

- [x] Exportación formal del informe (HTML)
- [x] Autenticación o aislamiento de informes por usuario

## Fase 5 — Mejoras de producto

- [x] Descarga del CSV limpio tras aceptar el plan
- [x] Documentación OpenAPI enriquecida
- [x] Autenticación por API key (opcional)

## Fase 6 — Limpieza avanzada

- [x] Clipping de outliers IQR en el plan de limpieza
- [x] Soporte de formatos adicionales (Parquet, Excel)
- [x] Estrategias de imputación configurables

## Fase 7 — Preparación de características

- [x] Estandarización opcional (z-score) de columnas numéricas en el plan de limpieza
- [x] Exposición del parámetro `scale_numeric` en el endpoint de carga de la API

## Fase 8 — Codificación de variables

- [x] Codificación de variables categóricas (one-hot o ordinal) opcional en el plan de limpieza

## Fase 9 — Refinamientos de codificación

- [x] Soporte de `drop_first` en codificación one-hot para evitar multicolinealidad

## Nota de estado (2026-10-29)

Implementación base de `dataclean/plan.py` restaurada (build_cleaning_plan, apply_plan, quality_delta). Todas las fases 0-9 verificadas contra pruebas.

## Fase 10 — Selección de características básica

- [x] Exclusión opcional de columnas numéricas de baja varianza (`drop_low_variance_threshold`)

## Fase 11 — Selección de características por correlación

- [x] Exclusión opcional de columnas numéricas altamente correlacionadas (`drop_high_correlation_threshold`)

## Fase 12 — Importancia de variables

- [x] Informe de importancia de variables derivado de los modelos no baseline (coeficientes absolutos o feature importances de árboles)

## Fase 13 — Candidatos por umbral de importancia

- [x] Parámetro opcional `importance_threshold` para reportar features de baja importancia máxima como candidatos a exclusión en el informe de modelado

## Fase 14 — Integración de baja importancia en el plan

- [x] Inclusión opcional de candidatos de baja importancia como acciones `drop_column` (razón `low_importance`) en el plan de limpieza mediante el parámetro `drop_low_importance`

## Fase 15 — Actualización del informe de modelado tras exclusiones por baja importancia

- [x] Re-ejecución de la comparación de modelos sobre el frame resultante cuando se aplican exclusiones por baja importancia, actualizando el informe de modelado

## Fase 16 — Persistencia y exposición explícita de importancias

- [x] Persistencia de las importancias calculadas dentro del informe almacenado y endpoint dedicado `GET /datasets/{id}/importances` para su consulta directa

## Fase 17 — Agregación de importancias de variables

- [x] Cálculo y exposición de importancias agregadas (máximo y media entre modelos no baseline) en el informe de modelado, endpoint de importancias e informe HTML

## Fase 18 — Visualización de importancias agregadas

- [x] Barras horizontales CSS de la importancia máxima agregada (top 15) en el informe HTML autocontenido

## Fase 19 — Persistencia tipada y plan target-aware

- [x] Archivo original y snapshot Parquet para evitar pérdida de tipos
- [x] Reconstrucción del dataset desde el snapshot al aceptar el plan
- [x] Modelado sobre la vista limpia aunque el plan no se haya aplicado
- [x] Protección de la variable objetivo en el plan de limpieza

## Fase 20 — Contrato de demo pública

- [x] Endpoints de salud, listado, borrado y vista previa
- [x] Parámetro explícito `target` en la carga
- [x] CORS, límite de subida y retención temporal configurables
- [x] Limpieza automática de datasets antiguos

## Fase 21 — EDA y validación de calidad

- [x] Inspección y clasificación de columnas (`inspect.py`)
- [x] Análisis exploratorio con distribuciones, correlaciones, series e insights (`eda.py`)
- [x] Reglas de validación, sugerencias y score multidimensional (`validation.py`)
- [x] Endpoints `GET /datasets/{id}/eda`, `GET /datasets/{id}/validation/suggestions` y `POST /datasets/{id}/validate`

## Fase 22 — Asesor de modelos y análisis no supervisado

- [x] Módulo `dataclean/advisor.py` con `suggest_modeling_strategy` que recomienda estrategia supervisada o no supervisada, viabilidad de clustering y acciones concretas a partir del perfil de datos y de los informes de objetivo/modelado
- [x] Pruebas unitarias de recomendaciones para casos con objetivo, sin objetivo y datos insuficientes

## Fase 23 — Exposición del asesor de modelos

- [x] Endpoint `GET /datasets/{id}/advisor` que expone `suggest_modeling_strategy`
- [x] Evaluación mínima de clustering (KMeans + silueta) cuando es viable
- [x] Inclusión de las recomendaciones y resultados de clustering en el informe HTML
- [x] Pruebas de API para el endpoint de asesor

## Fase 24 — Persistencia del asesor de modelos

- [x] Cálculo y almacenamiento del asesor en el registro del dataset al cargar
- [x] Actualización del asesor sobre la vista limpia al aceptar el plan
- [x] Reutilización del asesor persistido en el endpoint y en el informe HTML para evitar recomputación

## Fase 25 — Exposición de etiquetas de clustering

- [x] Inclusión de las etiquetas de cluster del mejor k en el resultado de clustering del asesor
- [x] Endpoint `GET /datasets/{id}/clusters` para consultar las asignaciones de cluster
- [x] Pruebas que verifican la disponibilidad de etiquetas

## Fase 26 — Descarga del CSV limpio con etiquetas de cluster opcionales

- [x] Endpoint `GET /datasets/{id}/download` que retorna el dataset limpio en CSV
- [x] Parámetro opcional `include_clusters` para añadir columna de etiquetas cuando es viable
- [x] Pruebas de API para el endpoint de descarga
