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
- [ ] Persistencia de informes
