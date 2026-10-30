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
