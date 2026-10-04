# Roadmap — DataClean AI

## Fase 0 — núcleo (esta entrega)
- [x] Perfil de columnas
- [x] Issues de calidad con severidad y recomendación
- [x] CLI `python -m dataclean.cli archivo.csv`
- [x] Test mínimo

## Fase 1 — limpieza aplicada
- [ ] Plan explícito (qué columna, qué acción, por qué)
- [ ] Aplicar plan y exportar CSV + diff de calidad
- [ ] Reglas: drop duplicados, imputar mediana/moda, marcar nulos, excluir id/constante

## Fase 2 — modelado condicional
- [ ] Detectar target numérico vs categórico
- [ ] Comparar baselines (mayoría / media) contra 2 modelos simples
- [ ] Informe de métrica y advertencia si n es chico o el target está desbalanceado

## Fase 3 — producto
- [ ] API de carga
- [ ] UI para ver issues y aceptar el plan
- [ ] Persistencia de informes
