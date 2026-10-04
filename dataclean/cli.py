from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dataclean.profile import profile_dataframe
from dataclean.quality import detect_issues


def analyze(path: str) -> dict:
    df = pd.read_csv(path)
    profile = profile_dataframe(df)
    issues = detect_issues(df)
    high = sum(1 for i in issues if i["severity"] in {"high", "critical"})
    return {
        "source": path,
        "profile": profile,
        "issues": issues,
        "summary": {
            "issue_count": len(issues),
            "high_or_critical": high,
            "ready_for_modeling": high == 0 and profile["rows"] >= 30,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="DataClean AI — perfil y calidad de un CSV")
    parser.add_argument("csv", help="Ruta al CSV")
    parser.add_argument("--out", help="Guardar el informe JSON")
    args = parser.parse_args()
    report = analyze(args.csv)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
