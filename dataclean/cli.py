from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dataclean.advisor import suggest_modeling_strategy
from dataclean.io import load_dataframe
from dataclean.models import compare_models
from dataclean.plan import apply_plan, build_cleaning_plan, quality_delta
from dataclean.profile import profile_dataframe
from dataclean.quality import detect_issues
from dataclean.target import detect_target


def analyze(
    path: str,
    apply: bool = False,
    target: str | None = None,
    imputation_strategies: dict | None = None,
    scale_numeric: bool = False,
    encode_categorical: str | None = None,
    onehot_drop_first: bool = False,
    drop_low_variance_threshold: float | None = None,
    drop_high_correlation_threshold: float | None = None,
    importance_threshold: float | None = None,
    drop_low_importance: bool = False,
    clip_outliers_iqr_multiplier: float | None = 1.5,
    bootstrap_resamples: int = 20,
) -> tuple[dict, pd.DataFrame | None]:
    df = load_dataframe(path)
    return analyze_frame(
        df,
        source=path,
        apply=apply,
        target=target,
        imputation_strategies=imputation_strategies,
        scale_numeric=scale_numeric,
        encode_categorical=encode_categorical,
        onehot_drop_first=onehot_drop_first,
        drop_low_variance_threshold=drop_low_variance_threshold,
        drop_high_correlation_threshold=drop_high_correlation_threshold,
        importance_threshold=importance_threshold,
        drop_low_importance=drop_low_importance,
        clip_outliers_iqr_multiplier=clip_outliers_iqr_multiplier,
        bootstrap_resamples=bootstrap_resamples,
    )


def analyze_frame(
    df: pd.DataFrame,
    source: str,
    apply: bool = False,
    target: str | None = None,
    imputation_strategies: dict | None = None,
    scale_numeric: bool = False,
    encode_categorical: str | None = None,
    onehot_drop_first: bool = False,
    drop_low_variance_threshold: float | None = None,
    drop_high_correlation_threshold: float | None = None,
    importance_threshold: float | None = None,
    drop_low_importance: bool = False,
    clip_outliers_iqr_multiplier: float | None = 1.5,
    bootstrap_resamples: int = 20,
) -> tuple[dict, pd.DataFrame | None]:
    profile = profile_dataframe(df)
    issues = detect_issues(df)
    target_report = detect_target(df, target=target)
    plan = build_cleaning_plan(
        df,
        imputation_strategies=imputation_strategies,
        scale_numeric=scale_numeric,
        encode_categorical=encode_categorical,
        onehot_drop_first=onehot_drop_first,
        drop_low_variance_threshold=drop_low_variance_threshold,
        drop_high_correlation_threshold=drop_high_correlation_threshold,
        target=target_report.get("column"),
        clip_outliers_iqr_multiplier=clip_outliers_iqr_multiplier,
    )
    high = sum(1 for issue in issues if issue["severity"] in {"high", "critical"})
    report = {
        "source": source,
        "profile": profile,
        "issues": issues,
        "plan": plan,
        "target": target_report,
        "summary": {
            "issue_count": len(issues),
            "high_or_critical": high,
            "plan_steps": len(plan),
            "ready_for_modeling": high == 0 and profile["rows"] >= 30 and target_report["found"],
            "target_column": target_report["column"],
            "target_task": target_report["task"],
        },
    }

    # El modelado se calcula siempre sobre una vista limpia. El resultado solo
    # se persiste como "applied" cuando el usuario acepta el plan.
    cleaned_preview = apply_plan(df, plan)
    cleaned_target = detect_target(
        cleaned_preview, target=target or target_report.get("column")
    )
    report["modeling"] = compare_models(
        cleaned_preview, cleaned_target, importance_threshold=importance_threshold
    )

    # Optionally incorporate low-importance candidates as drop steps in the plan
    if (
        drop_low_importance
        and importance_threshold is not None
        and importance_threshold > 0
        and report["modeling"].get("low_importance_candidates")
    ):
        candidates = report["modeling"]["low_importance_candidates"]
        current_cols = set(cleaned_preview.columns)
        existing_drops = {s.get("column") for s in plan if s.get("action") == "drop_column"}
        added = False
        for cand in candidates:
            feat = cand["feature"]
            if feat in current_cols and feat not in existing_drops:
                plan.append({
                    "column": feat,
                    "action": "drop_column",
                    "justification": (
                        f"La columna '{feat}' presenta importancia máxima "
                        f"{cand['max_importance']:.6f} inferior al umbral {importance_threshold}."
                    ),
                    "params": {
                        "reason": "low_importance",
                        "max_importance": cand["max_importance"],
                        "threshold": importance_threshold,
                    },
                })
                existing_drops.add(feat)
                added = True
        if added:
            # Re-apply the full updated plan on the original frame
            cleaned_preview = apply_plan(df, plan)
            cleaned_target = detect_target(
                cleaned_preview, target=target or target_report.get("column")
            )
            report["modeling"] = compare_models(
                cleaned_preview,
                cleaned_target,
                importance_threshold=importance_threshold,
            )

    # Integración del asesor de estrategias de modelado
    report["advisor"] = suggest_modeling_strategy(
        cleaned_preview,
        cleaned_target,
        report["modeling"],
        n_bootstrap=bootstrap_resamples,
    )

    cleaned = None
    if apply:
        after_profile = profile_dataframe(cleaned_preview)
        after_issues = detect_issues(cleaned_preview)
        report["applied"] = {
            "profile": after_profile,
            "issues": after_issues,
            "quality_delta": quality_delta(
                {
                    "rows": profile["rows"],
                    "columns": profile["columns"],
                    "duplicate_rows": profile["duplicate_rows"],
                    "issue_count": len(issues),
                },
                {
                    "rows": after_profile["rows"],
                    "columns": after_profile["columns"],
                    "duplicate_rows": after_profile["duplicate_rows"],
                    "issue_count": len(after_issues),
                },
            ),
            "target": cleaned_target,
        }
        cleaned = cleaned_preview

    report["summary"]["model_status"] = report["modeling"]["status"]
    report["summary"]["model_winner"] = report["modeling"]["winner"]
    report["summary"]["plan_steps"] = len(plan)
    return report, cleaned


def main() -> None:
    parser = argparse.ArgumentParser(description="DataClean AI — perfil, calidad, plan, objetivo y modelos")
    parser.add_argument("file", help="Ruta al archivo tabular (CSV, Excel, Parquet)")
    parser.add_argument("--out", help="Guardar el informe JSON")
    parser.add_argument("--apply", action="store_true", help="Aplicar el plan y añadir el delta de calidad")
    parser.add_argument("--cleaned", help="Ruta del CSV limpio (requiere --apply)")
    parser.add_argument("--target", help="Columna objetivo; si se omite, se infiere")
    parser.add_argument(
        "--impute-numeric",
        choices=["median", "mean", "mode", "constant"],
        default=None,
        help="Estrategia de imputación por defecto para columnas numéricas",
    )
    parser.add_argument(
        "--impute-categorical",
        choices=["mode", "median", "mean", "constant"],
        default=None,
        help="Estrategia de imputación por defecto para columnas categóricas",
    )
    parser.add_argument(
        "--impute-constant-value",
        default=None,
        help="Valor constante a usar cuando la estrategia es constant (numérico o categórico)",
    )
    parser.add_argument(
        "--scale-numeric",
        action="store_true",
        help="Incluir estandarización z-score de columnas numéricas en el plan",
    )
    parser.add_argument(
        "--encode-categorical",
        choices=["onehot", "ordinal"],
        default=None,
        help="Codificación opcional de columnas categóricas: onehot o ordinal (por frecuencia)",
    )
    parser.add_argument(
        "--onehot-drop-first",
        action="store_true",
        help="Al usar one-hot, omitir la primera categoría ordenada como referencia",
    )
    parser.add_argument(
        "--drop-low-variance-threshold",
        type=float,
        default=None,
        help="Excluir columnas numéricas cuyo desvío estándar (población) sea inferior a este umbral",
    )
    parser.add_argument(
        "--drop-high-correlation-threshold",
        type=float,
        default=None,
        help="Excluir columnas numéricas con |correlación| absoluta superior o igual a este umbral respecto a otra",
    )
    parser.add_argument(
        "--importance-threshold",
        type=float,
        default=None,
        help="Umbral de importancia: features cuya importancia máxima en modelos no baseline sea inferior se reportan como candidatos a exclusión",
    )
    parser.add_argument(
        "--drop-low-importance",
        action="store_true",
        help="Incluir automáticamente en el plan de limpieza las columnas cuya importancia máxima sea inferior al umbral (requiere --importance-threshold)",
    )
    parser.add_argument(
        "--clip-outliers-iqr-multiplier",
        type=float,
        default=1.5,
        help="Multiplicador IQR para clipping de outliers (por defecto 1.5; <=0 desactiva el clipping)",
    )
    parser.add_argument(
        "--bootstrap-resamples",
        type=int,
        default=20,
        help="Número de remuestreos bootstrap para la evaluación de estabilidad de la silueta en el asesor (1-100, por defecto 20)",
    )
    args = parser.parse_args()
    strategies = {}
    if args.impute_numeric:
        strategies["__numeric__"] = args.impute_numeric
    if args.impute_categorical:
        strategies["__categorical__"] = args.impute_categorical
    if args.impute_constant_value is not None:
        # applied when strategy is constant
        strategies.setdefault("__numeric__", {})
        if isinstance(strategies["__numeric__"], str) and strategies["__numeric__"] == "constant":
            strategies["__numeric__"] = {"strategy": "constant", "value": args.impute_constant_value}
        strategies.setdefault("__categorical__", {})
        if isinstance(strategies["__categorical__"], str) and strategies["__categorical__"] == "constant":
            strategies["__categorical__"] = {"strategy": "constant", "value": args.impute_constant_value}
    report, cleaned = analyze(
        args.file,
        apply=args.apply or bool(args.cleaned),
        target=args.target,
        imputation_strategies=strategies or None,
        scale_numeric=args.scale_numeric,
        encode_categorical=args.encode_categorical,
        onehot_drop_first=args.onehot_drop_first,
        drop_low_variance_threshold=args.drop_low_variance_threshold,
        drop_high_correlation_threshold=args.drop_high_correlation_threshold,
        importance_threshold=args.importance_threshold,
        drop_low_importance=args.drop_low_importance,
        clip_outliers_iqr_multiplier=args.clip_outliers_iqr_multiplier,
        bootstrap_resamples=args.bootstrap_resamples,
    )
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    if args.cleaned:
        if cleaned is None:
            raise SystemExit("--cleaned requiere un plan aplicado")
        cleaned.to_csv(args.cleaned, index=False)
    print(text)


if __name__ == "__main__":
    main()
