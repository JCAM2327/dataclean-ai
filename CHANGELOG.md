# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

### Planeado
- Interfaz para revisar issues y aceptar el plan de limpieza.
- Persistencia de informes.

## [0.5.0] — 2026-10-09

### Añadido
- API de carga de datasets (`dataclean.api`): `POST /datasets` recibe un CSV y devuelve identificador, resumen y enlace al informe.
- El informe reutiliza perfil, issues, plan, objetivo y comparación de modelos. `apply` ejecuta el plan y expone el CSV limpio en `GET /datasets/{id}/cleaned`.
- Consulta de datasets cargados (`GET /datasets`, `GET /datasets/{id}`) y estado (`GET /health`).
- Validación de entrada: solo CSV, archivo no vacío, límite de 2 MB, UTF-8 y filas con el mismo número de campos.
- Registro en memoria. La persistencia de informes permanece pendiente.
- `analyze_frame` permite analizar un `DataFrame` sin escribir un archivo temporal.
- Pruebas de contrato en `tests/test_api.py`.

## [0.4.0] — 2026-10-08

### Añadido
- Comparación de baselines y dos modelos simples (`dataclean.models.compare_models`) sobre una partición de retención.
- Clasificación: baseline de clase mayoritaria, regresión logística y árbol de profundidad 3. Métricas: accuracy, F1 macro y F1 ponderado. Métrica primaria: F1 macro.
- Regresión: baseline de media de entrenamiento, regresión lineal y árbol de profundidad 3. Métricas: MAE, RMSE y R². Métrica primaria: RMSE.
- Informe de modelado con ganador, diferencia frente al baseline, features excluidas y advertencias (muestra menor a 30 filas, desbalance, partición no estratificada, conjunto de prueba pequeño).
- Omisiones explícitas si no hay objetivo, no hay filas suficientes, queda una sola clase o no quedan features.
- CLI: el informe JSON incluye `modeling`; el resumen expone `model_status` y `model_winner`. Si se aplica el plan, la comparación usa el dataset limpio.
- Dependencia `scikit-learn` y pruebas en `tests/test_models.py`.

## [0.3.0] — 2026-10-06

### Añadido
- Detección de variable objetivo (`dataclean.target.detect_target`): distingue objetivo numérico (regresión) y categórico (clasificación).
- Inferencia por alias de nombre (`objetivo`, `target`, `label`, `y`, `clase`, entre otros) y por cardinalidad; `--target` fija la columna y tiene prioridad.
- Exclusión de identificadores y constantes en la inferencia. El informe declara confianza, candidatos, clases y advertencias de muestra pequeña, desbalance o nulos elevados.
- CLI: el informe JSON incluye `target`; el resumen marca `ready_for_modeling` solo si hay objetivo utilizable.
- Pruebas de inferencia, objetivo explícito, columna inexistente y advertencias.

## [0.2.0] — 2026-10-05

### Añadido
- Plan de limpieza explícito (`dataclean.plan.build_cleaning_plan`): cada paso declara columna, acción y justificación.
- Reglas del plan: eliminar duplicados exactos, excluir constantes e identificadores, descartar columnas con 40% o más de nulos, imputar mediana o moda e incorporar indicador de faltante.
- Aplicación del plan (`apply_plan`) y delta de calidad (`quality_delta`) entre el dataset original y el limpio.
- CLI: el informe JSON incluye el plan; `--apply` y `--cleaned` exportan el CSV limpio y el informe de diferencias.
- Pruebas de construcción y aplicación del plan.

## [0.1.0] — 2026-10-04

### Añadido
- Módulo de perfilado de columnas (`dataclean.profile`): filas, tipos, nulos, valores únicos, duplicados y estadísticas numéricas.
- Detección de issues de calidad (`dataclean.quality`) con severidad y recomendación: nulos elevados, columnas constantes, posibles identificadores, outliers por IQR y filas duplicadas.
- Interfaz de línea de comandos (`python -m dataclean.cli`) para analizar un CSV y emitir informe JSON.
- Dataset de ejemplo (`examples/sample.csv`) y prueba unitaria mínima.
- Documentación inicial: README, ROADMAP y estructura de registro diario en `docs/diario/`.
