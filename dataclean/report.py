"""Renderizado de informes en HTML autocontenido."""

from __future__ import annotations

from collections import Counter
from html import escape
from typing import Any


def render_report_html(record: dict[str, Any]) -> str:
    """Genera un informe HTML completo a partir del registro del dataset.

    El HTML es autocontenido (estilos inline) y cubre resumen, issues, plan,
    objetivo, modelado y asesor cuando están presentes.
    """
    report = record.get("report") or {}
    summary = record.get("summary") or {}
    issues = report.get("issues") or []
    plan = report.get("plan") or []
    target = report.get("target") or {}
    modeling = report.get("modeling") or {}
    advisor = record.get("advisor") or {}
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
        ".bar-row{display:flex;align-items:center;margin:0.3rem 0;font-size:0.85rem}",
        ".bar-label{width:30%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}",
        ".bar-track{flex:1;background:#e2e8f0;height:1.2rem;border-radius:4px;overflow:hidden;margin:0 0.5rem}",
        ".bar{background:#3b82f6;height:100%;border-radius:4px}",
        ".bar-value{width:15%;text-align:right;font-variant-numeric:tabular-nums}",
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
        "<h2>Modelado</h2>",
        _modeling_section(modeling),
        "<h2>Asesor de modelos</h2>",
        _advisor_section(advisor),
        "</body>",
        "</html>",
    ]
    return "\n".join(parts)


def _summary_table(summary: dict[str, Any]) -> str:
    rows = [
        ("Filas", summary.get("rows") or summary.get("issue_count") and "—"),
        ("Issues", summary.get("issue_count")),
        ("Altos/críticos", summary.get("high_or_critical")),
        ("Pasos del plan", summary.get("plan_steps")),
        ("Objetivo", summary.get("target_column")),
        ("Tarea", summary.get("target_task")),
        ("Estado modelo", summary.get("model_status")),
        ("Ganador", summary.get("model_winner")),
    ]
    return _kv_table([(k, v) for k, v in rows if v is not None])


def _issues_table(issues: list[dict[str, Any]]) -> str:
    if not issues:
        return "<p>No se detectaron issues.</p>"
    headers = ["Columna", "Tipo", "Severidad", "Recomendación"]
    body = []
    for issue in issues:
        sev = str(issue.get("severity") or "")
        body.append(
            "<tr>"
            f"<td>{escape(str(issue.get('column') or ''))}</td>"
            f"<td>{escape(str(issue.get('type') or ''))}</td>"
            f'<td><span class="badge {sev}">{sev}</span></td>'
            f"<td>{escape(str(issue.get('recommendation') or ''))}</td>"
            "</tr>"
        )
    return _html_table(headers, body)


def _plan_table(plan: list[dict[str, Any]]) -> str:
    if not plan:
        return "<p>No hay pasos de limpieza.</p>"
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
    c = target.get("classes")
    classes_str = ", ".join(map(str, c)) if isinstance(c, (list, tuple)) else (str(c) if c is not None else "—")
    rows = [
        ("Columna", target.get("column")),
        ("Tarea", target.get("task")),
        ("Confianza", target.get("confidence")),
        ("Clases", classes_str),
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
        ("Ganador", modeling.get("winner")),
        ("Lift", modeling.get("lift_vs_baseline")),
    ]
    html = _kv_table(rows)
    for model in modeling.get("models") or []:
        imps = model.get("feature_importances")
        if imps:
            html += f"<h3>Importancia de variables — {escape(model.get('name') or '')}</h3>"
            headers = ["Feature", "Importancia"]
            body = []
            for item in imps[:15]:
                body.append(
                    "<tr>"
                    f"<td>{escape(str(item.get('feature') or ''))}</td>"
                    f"<td>{escape(str(item.get('importance') or ''))}</td>"
                    "</tr>"
                )
            html += _html_table(headers, body)
    agg = modeling.get("aggregated_importances")
    if agg:
        html += "<h3>Importancias agregadas (máximo y media entre modelos)</h3>"
        headers = ["Feature", "Máximo", "Media", "Modelos"]
        body = []
        for item in agg[:15]:
            body.append(
                "<tr>"
                f"<td>{escape(str(item.get('feature') or ''))}</td>"
                f"<td>{escape(str(item.get('max_importance') or ''))}</td>"
                f"<td>{escape(str(item.get('mean_importance') or ''))}</td>"
                f"<td>{escape(str(item.get('model_count') or ''))}</td>"
                "</tr>"
            )
        html += _html_table(headers, body)
        max_val = max((float(item.get("max_importance") or 0) for item in agg[:15]), default=1.0) or 1.0
        bars = []
        for item in agg[:15]:
            feat = escape(str(item.get("feature") or ""))
            val = float(item.get("max_importance") or 0)
            pct = min(100.0, (val / max_val) * 100.0)
            bars.append(
                f'<div class="bar-row">'
                f'<div class="bar-label" title="{feat}">{feat}</div>'
                f'<div class="bar-track"><div class="bar" style="width:{pct:.1f}%"></div></div>'
                f'<div class="bar-value">{val:.4f}</div>'
                f'</div>'
            )
        if bars:
            html += "<h4>Visualización (importancia máxima)</h4>" + "".join(bars)
    return html


def _advisor_section(advisor: dict[str, Any]) -> str:
    if not advisor:
        return "<p>Asesor no disponible.</p>"
    rows = [
        ("Estrategia", advisor.get("strategy")),
        ("Objetivo encontrado", "sí" if advisor.get("target_found") else "no"),
        ("Clustering viable", "sí" if advisor.get("clustering_viable") else "no"),
        ("Columnas numéricas", advisor.get("numeric_columns_count")),
        ("Filas", advisor.get("rows")),
    ]
    html = _kv_table(rows)
    html += f"<p>{escape(advisor.get('rationale') or '')}</p>"
    recs = advisor.get("recommendations") or []
    if recs:
        html += "<h3>Recomendaciones</h3><ul>"
        for r in recs:
            html += f"<li>{escape(str(r))}</li>"
        html += "</ul>"
    cr = advisor.get("clustering_results")
    if cr and isinstance(cr, dict) and "best_k" in cr:
        html += "<h3>Evaluación de clustering (KMeans)</h3>"
        html += _kv_table([
            ("Mejor k", cr.get("best_k")),
            ("Silueta", cr.get("best_silhouette")),
            ("Inercia", cr.get("best_inertia")),
            ("Davies-Bouldin", cr.get("best_davies_bouldin")),
            ("Calinski-Harabasz", cr.get("best_calinski_harabasz")),
            ("Muestras", cr.get("n_samples")),
        ])
        scores = cr.get("silhouette_scores") or {}
        if scores:
            html += "<p>Siluetas por k: " + ", ".join(f"k={k}: {v}" for k, v in scores.items()) + "</p>"
        labels = cr.get("labels")
        if labels and isinstance(labels, list) and len(labels) > 0:
            counts = Counter(labels)
            total = len(labels)
            html += "<h4>Distribución de etiquetas de cluster</h4>"
            headers = ["Cluster", "Conteo", "Porcentaje"]
            body = []
            for label in sorted(counts.keys()):
                count = counts[label]
                pct = (count / total) * 100
                body.append(
                    "<tr>"
                    f"<td>{escape(str(label))}</td>"
                    f"<td>{count}</td>"
                    f"<td>{pct:.1f}%</td>"
                    "</tr>"
                )
            html += _html_table(headers, body)
    return html


def _kv_table(rows: list[tuple[str, Any]]) -> str:
    body = []
    for key, value in rows:
        body.append(f"<tr><th>{escape(str(key))}</th><td>{escape(str(value) if value is not None else '—')}</td></tr>")
    return _html_table(["Campo", "Valor"], body)


def _html_table(headers: list[str], body_rows: list[str]) -> str:
    head = "".join(f"<th>{escape(h)}</th>" for h in headers)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"
