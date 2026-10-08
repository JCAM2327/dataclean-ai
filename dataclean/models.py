from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

MIN_ROWS = 8
SMALL_SAMPLE = 30
IMBALANCE_RATIO = 0.2
DEFAULT_TEST_SIZE = 0.25
RANDOM_STATE = 42


def compare_models(
    df: pd.DataFrame,
    target_report: dict[str, Any],
    test_size: float = DEFAULT_TEST_SIZE,
    random_state: int = RANDOM_STATE,
) -> dict[str, Any]:
    """Compare a baseline against two simple models on a held-out split.

    Classification uses the majority class as baseline, logistic regression and
    a depth-limited tree. Regression uses the training mean, linear regression
    and a depth-limited tree. Metrics and warnings are part of the same report.
    """
    if not target_report.get("found"):
        return _skipped(
            "No hay variable objetivo utilizable; no se ajustan modelos.",
            ["target_not_found"],
            target_report,
        )

    column = str(target_report["column"])
    task = target_report.get("task")
    if column not in df.columns or task not in {"classification", "regression"}:
        return _skipped(
            "El objetivo declarado no está en el dataset o la tarea no es válida.",
            ["target_missing"],
            target_report,
        )

    frame = df.dropna(subset=[column]).copy()
    warnings = list(target_report.get("warnings") or [])
    if len(frame) < MIN_ROWS:
        return _skipped(
            f"Se requieren al menos {MIN_ROWS} filas con objetivo observado.",
            _unique(warnings + ["insufficient_rows"]),
            target_report,
        )

    features, dropped = _feature_frame(frame, column)
    if features.shape[1] == 0:
        return _skipped(
            "No quedan features tras excluir el objetivo, identificadores y constantes.",
            _unique(warnings + ["insufficient_features"]),
            target_report,
        )

    y = frame[column]
    if task == "classification":
        y = y.astype(str)
        if int(y.nunique()) < 2:
            return _skipped(
                "El objetivo observado tiene una sola clase.",
                _unique(warnings + ["single_class"]),
                target_report,
            )
    else:
        y = pd.to_numeric(y, errors="coerce")
        keep = y.notna()
        features = features.loc[keep]
        y = y.loc[keep]
        if len(y) < MIN_ROWS:
            return _skipped(
                "El objetivo numérico no tiene suficientes valores observados.",
                _unique(warnings + ["insufficient_rows"]),
                target_report,
            )

    stratify = y if task == "classification" and _can_stratify(y, test_size) else None
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )
    x_train_m, x_test_m = _matrices(x_train, x_test)

    if task == "classification":
        fitted = _fit_classification(x_train_m, x_test_m, y_train, y_test)
        primary = "f1_macro"
        higher_is_better = True
    else:
        fitted = _fit_regression(x_train_m, x_test_m, y_train, y_test)
        primary = "rmse"
        higher_is_better = False

    if len(frame) < SMALL_SAMPLE and "small_sample" not in warnings:
        warnings.append("small_sample")
    if task == "classification":
        minority = float(y.value_counts(normalize=True).min())
        if minority < IMBALANCE_RATIO and "class_imbalance" not in warnings:
            warnings.append("class_imbalance")
    if stratify is None and task == "classification":
        warnings.append("unstratified_split")
    if int(y_test.shape[0]) < 3:
        warnings.append("small_test_set")

    baseline = fitted[0]
    models = fitted[1:]
    winner = _winner(fitted, primary, higher_is_better)
    lift = _lift(winner, baseline, primary, higher_is_better)
    return {
        "status": "compared",
        "task": task,
        "column": column,
        "rows_used": int(len(frame)),
        "features_used": int(features.shape[1]),
        "features_dropped": dropped,
        "split": {
            "test_size": test_size,
            "train_rows": int(len(y_train)),
            "test_rows": int(len(y_test)),
            "random_state": random_state,
            "stratified": stratify is not None,
        },
        "primary_metric": primary,
        "higher_is_better": higher_is_better,
        "baseline": baseline,
        "models": models,
        "winner": winner["name"],
        "beats_baseline": lift > 0,
        "lift_vs_baseline": round(lift, 6),
        "warnings": _unique(warnings),
        "rationale": _rationale(task, baseline["name"], winner["name"], lift, primary),
    }


def _fit_classification(x_train, x_test, y_train, y_test) -> list[dict[str, Any]]:
    specs = [
        ("baseline_mayoria", DummyClassifier(strategy="most_frequent")),
        ("regresion_logistica", LogisticRegression(max_iter=500)),
        ("arbol_profundidad_3", DecisionTreeClassifier(max_depth=3, random_state=RANDOM_STATE)),
    ]
    reports = []
    for name, estimator in specs:
        estimator.fit(x_train, y_train)
        pred = estimator.predict(x_test)
        reports.append({
            "name": name,
            "role": "baseline" if name.startswith("baseline") else "model",
            "metrics": {
                "accuracy": round(float(accuracy_score(y_test, pred)), 6),
                "f1_macro": round(float(f1_score(y_test, pred, average="macro", zero_division=0)), 6),
                "f1_weighted": round(float(f1_score(y_test, pred, average="weighted", zero_division=0)), 6),
            },
        })
    return reports


def _fit_regression(x_train, x_test, y_train, y_test) -> list[dict[str, Any]]:
    specs = [
        ("baseline_media", DummyRegressor(strategy="mean")),
        ("regresion_lineal", LinearRegression()),
        ("arbol_profundidad_3", DecisionTreeRegressor(max_depth=3, random_state=RANDOM_STATE)),
    ]
    reports = []
    for name, estimator in specs:
        estimator.fit(x_train, y_train)
        pred = estimator.predict(x_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        reports.append({
            "name": name,
            "role": "baseline" if name.startswith("baseline") else "model",
            "metrics": {
                "mae": round(float(mean_absolute_error(y_test, pred)), 6),
                "rmse": round(rmse, 6),
                "r2": round(float(r2_score(y_test, pred)), 6),
            },
        })
    return reports


def _feature_frame(df: pd.DataFrame, target: str) -> tuple[pd.DataFrame, list[str]]:
    dropped: list[str] = []
    keep: list[str] = []
    n_rows = len(df)
    for name in df.columns:
        if name == target:
            continue
        series = df[name]
        nunique = int(series.nunique(dropna=True))
        if nunique <= 1 or _is_identifier(series, nunique, n_rows):
            dropped.append(str(name))
            continue
        keep.append(str(name))
    return df[keep].copy(), dropped


def _matrices(x_train: pd.DataFrame, x_test: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    train = x_train.copy()
    test = x_test.copy()
    for column in train.columns:
        numeric = pd.to_numeric(train[column], errors="coerce")
        if float(numeric.notna().mean()) >= 0.8:
            median = float(numeric.median()) if numeric.notna().any() else 0.0
            train[column] = pd.to_numeric(train[column], errors="coerce").fillna(median)
            test[column] = pd.to_numeric(test[column], errors="coerce").fillna(median)
        else:
            mode = train[column].mode(dropna=True)
            fill = "missing" if mode.empty else mode.iloc[0]
            train[column] = train[column].fillna(fill).astype(str)
            test[column] = test[column].fillna(fill).astype(str)
    encoded_train = pd.get_dummies(train, drop_first=False)
    encoded_test = pd.get_dummies(test, drop_first=False)
    encoded_test = encoded_test.reindex(columns=encoded_train.columns, fill_value=0)
    return encoded_train.to_numpy(dtype=float), encoded_test.to_numpy(dtype=float)


def _can_stratify(y: pd.Series, test_size: float) -> bool:
    counts = y.value_counts()
    test_rows = max(1, int(round(len(y) * test_size)))
    return int(counts.min()) >= 2 and test_rows >= int(counts.shape[0])


def _winner(reports: list[dict[str, Any]], metric: str, higher_is_better: bool) -> dict[str, Any]:
    return sorted(
        reports,
        key=lambda item: item["metrics"][metric],
        reverse=higher_is_better,
    )[0]


def _lift(winner: dict[str, Any], baseline: dict[str, Any], metric: str, higher_is_better: bool) -> float:
    best = float(winner["metrics"][metric])
    base = float(baseline["metrics"][metric])
    return best - base if higher_is_better else base - best


def _is_identifier(series: pd.Series, nunique: int, n_rows: int) -> bool:
    name = str(series.name).lower()
    named_id = name in {"id", "uuid", "guid"} or name.endswith("_id")
    unique_text = nunique == n_rows and (
        pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)
    )
    return named_id or unique_text


def _rationale(task: str, baseline: str, winner: str, lift: float, metric: str) -> str:
    direction = "supera" if lift > 0 else "no supera"
    if task == "classification":
        return (
            f"Clasificación: baseline de clase mayoritaria ({baseline}). "
            f"El mejor ajuste ({winner}) {direction} al baseline en {metric} "
            f"(diferencia {round(lift, 4)})."
        )
    return (
        f"Regresión: baseline de media de entrenamiento ({baseline}). "
        f"El mejor ajuste ({winner}) {direction} al baseline en {metric} "
        f"(diferencia {round(lift, 4)})."
    )


def _skipped(rationale: str, warnings: list[str], target_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "skipped",
        "task": target_report.get("task"),
        "column": target_report.get("column"),
        "rows_used": 0,
        "features_used": 0,
        "features_dropped": [],
        "split": None,
        "primary_metric": None,
        "higher_is_better": None,
        "baseline": None,
        "models": [],
        "winner": None,
        "beats_baseline": False,
        "lift_vs_baseline": None,
        "warnings": warnings,
        "rationale": rationale,
    }


def _unique(items: list[str]) -> list[str]:
    seen: list[str] = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen
