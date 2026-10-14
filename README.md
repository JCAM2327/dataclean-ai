# DataClean AI

Herramienta para perfilar datasets tabulares, detectar issues de calidad, generar y aplicar planes de limpieza, detectar variable objetivo y comparar modelos baseline.

## Uso por línea de comandos

```bash
python -m dataclean.cli examples/sample.csv
```

## API

Servidor FastAPI con aislamiento de informes por usuario.

- Cabecera obligatoria: `X-User-Id`
- `POST /datasets` — carga CSV y genera informe
- `GET /datasets/{id}` — consulta el registro
- `POST /datasets/{id}/accept` — aplica el plan de limpieza
- `GET /datasets/{id}/report.html` — informe HTML autocontenido

```bash
uvicorn dataclean.api:app --reload
```

Versión actual: 0.9.0
