"""Renderizado de informes en HTML autocontenido."""

from __future__ import annotations

from html import escape
from typing import Any


def render_report_html(record: dict[str, Any]) -> str:
    """Genera un informe HTML completo a partir del registro del dataset.

    El HTML es autocontenido (estilos inline) y cubre resumen, issues, plan,
    objetivo y modelado cuando están presentes.
    """
    report = record.get("report") or {}
    summary = record.get("summary") or {}
    issues = report.get("issues") or []
    plan = report.get("plan") or []
    target = report.get("target") or {}
    modeling = report.get("modeling") or {}
    applied = record.get("applied", False)

    title = escape(record.get("filename") or "Informe de dataset")
    dataset_id = escape(record.get("dataset_id") or "")
    created = escape(record.get("created_at") or "")

    parts = [
        "<!DOCTYPE html>",
        '<html lang="es">',
        "<head>",
        '<meta charset="utf-8">',
        f"<title>Informe — {title}</title>",
        "<style>",
        "body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;line-height:1.5;margin:2rem;color:#1a1a1a;background:#fafafa}",
        "h1,h2{color:#0f172a}table{border-collapse:collapse;width:100%;margin:1rem 0}th,td{border:1px solid #e2e8f0;padding:0.4rem 0.6rem;text-align:left}th{background:#f1f5f9}",
        ".meta{color:#475569;font-size:0.9rem}.badge{display:inline-block;padding:0.1rem 0.5rem;border-radius:999px;font-size:0.8rem;background:#e2e8f0}",
        ".high{background:#fee2e2;color:#991b1b}.critical{background:#fecaca;color:#7f1d1d}.medium{background:#fef3c7;color:#92400e}.low{background:#dcfce7;color:#166534}",
        "</style>",
        "</head>",
        "<body>",
        f"<h1>Informe de limpieza — {title}</h1>",
        f'<p class="meta">Identificador: <code>{dataset_id}</code> · Creado: {created} · Aplicado: {"sí" if applied else "no"}</p>',
        "<h2>Resumen</h2>",
        _summary_table(summary),
        "<h2>Issues de calidad</h2>",
        _issues_table(issues),
        "<h2>Plan de limpieza</h2>",
        _plan_table(plan),
        "<h2>Variable objetivo</h2>",
        _target_section(target),
        "<h2>Comparación de modelos</h2>",
        _modeling_section(modeling),
        "</body>",
        "</html>",
    ]
    return "\n".join(parts)


def _summary_table(summary: dict[str, Any]) -> str:
    rows = [
        ("Issues", summary.get("issue_count")),
        ("Alta/crítica", summary.get("high_or_critical")),
        ("Pasos del plan", summary.get("plan_steps")),
        ("Listo para modelar", "sí" if summary.get("ready_for_modeling") else "no"),
        ("Columna objetivo", summary.get("target_column") or "—"),
        ("Tarea", summary.get("target_task") or "—"),
        ("Estado del modelo", summary.get("model_status") or "—"),
        ("Ganador", summary.get("model_winner") or "—"),
    ]
    return _kv_table(rows)


def _issues_table(issues: list[dict[str, Any]]) -> str:
    if not issues:
        return "<p>No se detectaron issues.</p>"
    headers = ["Columna", "Tipo", "Severidad", "Detalle", "Recomendación"]
    body = []
    for issue in issues:
        sev = escape(str(issue.get("severity") or ""))
        body.append(
            "<tr>"
            f"<td>{escape(str(issue.get('column') or ''))}</td>"
            f"<td>{escape(str(issue.get('type') or ''))}</td>"
            f'<td><span class="badge {sev}">{sev}</span></td>'
            f"<td>{escape(str(issue.get('detail') or ''))}</td>"
            f"<td>{escape(str(issue.get('recommendation') or ''))}</td>"
            "</tr>"
        )
    return _html_table(headers, body)


def _plan_table(plan: list[dict[str, Any]]) -> str:
    if not plan:
        return "<p>El plan está vacío.</p>"
    headers = ["Columna", "Acción", "Justificación"]
    body = []
    for step in plan:
        body.append(
            "<tr>"
            f"<td>{escape(str(step.get('column') or ''))}</td>"
            f"<td>{escape(str(step.get('action') or ''))}</td>"
            f"<td>{escape(str(step.get('justification') or ''))}</td>"
            "</tr>"
        )
    return _html_table(headers, body)


def _target_section(target: dict[str, Any]) -> str:
    if not target.get("found"):
        return f"<p>{escape(target.get('rationale') or 'No se detectó objetivo utilizable.')}</p>"
    rows = [
        ("Columna", target.get("column")),
        ("Tarea", target.get("task")),
        ("Confianza", target.get("confidence")),
        ("Clases", ", ".join(map(str, target.get("classes") or [])) or "—"),
    ]
    warnings = target.get("warnings") or []
    extra = ""
    if warnings:
        extra = "<p>Advertencias: " + ", ".join(escape(str(w)) for w in warnings) + "</p>"
    return _kv_table(rows) + extra


def _modeling_section(modeling: dict[str, Any]) -> str:
    if modeling.get("status") != "compared":
        return f"<p>{escape(modeling.get('rationale') or 'Modelado omitido.')}</p>"
    rows = [
        ("Estado", modeling.get("status")),
        ("Tarea", modeling.get("task")),
        ("Filas usadas", modeling.get("rows_used")),
        ("Features usadas", modeling.get("features_used")),
        ("Métrica primaria", modeling.get("primary_metric")),
        ("Ganador", modeling.get("winner")),
        ("Supera baseline", "sí" if modeling.get("beats_baseline") else "no"),
        ("Diferencia vs baseline", modeling.get("lift_vs_baseline")),
    ]
    models_html = ""
    models = modeling.get("models") or []
    if models or modeling.get("baseline"):
        headers = ["Nombre", "Rol"] + list((modeling.get("baseline") or models[0]).get("metrics", {}).keys())
        body = []
        items = ([modeling.get("baseline")] + models) if modeling.get("baseline") else models
        for item in items:
            if not item:
                continue
            metrics = item.get("metrics") or {}
            cells = [
                escape(str(item.get("name") or "")),
                escape(str(item.get("role") or "")),
            ] + [escape(str(metrics.get(k, "—"))) for k in headers[2:]]
            body.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
        models_html = "<h3>Resultados</h3>" + _html_table(headers, body)
    warnings = modeling.get("warnings") or []
    warn_html = ""
    if warnings:
        warn_html = "<p>Advertencias: " + ", ".join(escape(str(w)) for w in warnings) + "</p>"
    return _kv_table(rows) + models_html + warn_html + f"<p>{escape(modeling.get('rationale') or '')}</p>"


def _kv_table(rows: list[tuple[str, Any]]) -> str:
    body = [
        f"<tr><th>{escape(k)}</th><td>{escape(str(v) if v is not None else '—')}</td></tr>"
        for k, v in rows
    ]
    return '<table><tbody>' + "".join(body) + "</tbody></table>"


def _html_table(headers: list[str], body_rows: list[str]) -> str:
    head = "<tr>" + "".join(f"<th>{escape(h)}</th>" for h in headers) + "</tr>"
    return "<table>" + head + "".join(body_rows) + "</table>"
