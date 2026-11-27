# Ejemplos de uso de la CLI

La interfaz de línea de comandos permite analizar datasets tabulares y generar informes JSON con perfil, calidad, plan de limpieza, detección de objetivo, comparación de modelos y asesor de estrategias.

## Ejemplo básico

```bash
python -m dataclean.cli examples/sample.csv
```

## Con remuestreos bootstrap personalizados

```bash
python -m dataclean.cli examples/sample.csv --bootstrap-resamples 30 --out informe.json
```

## Aplicando el plan y guardando el CSV limpio

```bash
python -m dataclean.cli examples/sample.csv --apply --cleaned limpio.csv --target objetivo
```

## Con opciones de preprocesamiento

```bash
python -m dataclean.cli datos.csv \
  --scale-numeric \
  --encode-categorical onehot \
  --drop-low-variance-threshold 0.01 \
  --importance-threshold 0.01 \
  --bootstrap-resamples 40
```

## Ayuda completa

```bash
python -m dataclean.cli --help
```
