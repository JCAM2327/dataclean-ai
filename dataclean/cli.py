from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dataclean.plan import apply_plan, build_cleaning_plan, quality_delta
from dataclean.profile import profile_dataframe
from dataclean.quality import detect_issues


def analyze(path: str, apply: bool = False) -> tuple[dict, pd.DataFrame | None]:
    df = pd.read_csv(path)
    profile = profile_dataframe(df)
    issues = detect_issues(df)
    plan = build_cleaning_plan(df)
    high = sum(1 for issue in issues if issue["severity"] in {"high", "critical"})
    report = {
        "source": path,
        "profile": profile,
        "issues": issues,
        "plan": plan,
        "summary": {
            "issue_count": len(issues),
            "high_or_critical": high,
            "plan_steps": len(plan),
            "ready_for_modeling": high == 0 and profile["rows"] >= 30,
        },
    }
    cleaned = None
    if apply:
        cleaned = apply_plan(df, plan)
        after_profile = profile_dataframe(cleaned)
        after_issues = detect_issues(cleaned)
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
        }
    return report, cleaned


def main() -> None:
    parser = argparse.ArgumentParser(description="DataClean AI — perfil, calidad y plan de limpieza")
    parser.add_argument("csv", help="Ruta al CSV")
    parser.add_argument("--out", help="Guardar el informe JSON")
    parser.add_argument("--apply", action="store_true", help="Aplicar el plan y añadir el delta de calidad")
    parser.add_argument("--cleaned", help="Ruta del CSV limpio (requiere --apply)")
    args = parser.parse_args()
    report, cleaned = analyze(args.csv, apply=args.apply or bool(args.cleaned))
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
