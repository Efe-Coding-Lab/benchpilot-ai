from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import TestRun


@dataclass
class AnalysisSummary:
    total_measurements: int
    failed_measurements: int
    anomalous_measurements: int
    pass_rate: float
    top_suspicious_tests: list[dict[str, Any]]
    signal_health: list[dict[str, Any]]
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _frame_from_runs(runs: list[TestRun]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": r.id,
                "run_id": r.run_id,
                "test_name": r.test_name,
                "signal": r.signal,
                "value": r.value,
                "lower_bound": r.lower_bound,
                "upper_bound": r.upper_bound,
                "duration_ms": r.duration_ms,
                "temperature_c": r.temperature_c,
                "supply_v": r.supply_v,
                "computed_status": r.computed_status,
            }
            for r in runs
        ]
    )


def analyze_runs(session: Session, minimum_ml_rows: int = 12) -> AnalysisSummary:
    runs = list(session.scalars(select(TestRun).order_by(TestRun.timestamp.asc())))
    if not runs:
        return AnalysisSummary(0, 0, 0, 0.0, [], [], ["Ingest measurements before running analytics."])

    df = _frame_from_runs(runs)
    span = (df["upper_bound"] - df["lower_bound"]).replace(0, np.nan)
    midpoint = (df["upper_bound"] + df["lower_bound"]) / 2.0
    df["normalized_offset"] = ((df["value"] - midpoint) / span).fillna(0.0)
    df["boundary_margin"] = np.minimum(
        df["value"] - df["lower_bound"],
        df["upper_bound"] - df["value"],
    ) / span.replace(0, np.nan)
    df["boundary_margin"] = df["boundary_margin"].fillna(0.0)

    anomaly_flags = np.zeros(len(df), dtype=bool)
    anomaly_scores = np.zeros(len(df), dtype=float)
    if len(df) >= minimum_ml_rows:
        features = df[["normalized_offset", "duration_ms", "temperature_c", "supply_v"]].copy()
        for column in features.columns:
            std = float(features[column].std()) or 1.0
            features[column] = (features[column] - float(features[column].mean())) / std
        contamination = min(0.18, max(0.05, 2.0 / len(df)))
        model = IsolationForest(n_estimators=160, contamination=contamination, random_state=42)
        labels = model.fit_predict(features)
        anomaly_flags = labels == -1
        anomaly_scores = -model.score_samples(features)

    df["anomaly"] = anomaly_flags
    df["anomaly_score"] = anomaly_scores

    by_id = {r.id: r for r in runs}
    for row in df[["id", "anomaly", "anomaly_score"]].to_dict(orient="records"):
        model_row = by_id[int(row["id"])]
        model_row.anomaly = bool(row["anomaly"])
        model_row.anomaly_score = float(row["anomaly_score"])
    session.flush()

    df["failed"] = df["computed_status"].eq("FAIL")
    grouped = (
        df.groupby(["test_name", "signal"], as_index=False)
        .agg(
            runs=("id", "count"),
            failures=("failed", "sum"),
            anomalies=("anomaly", "sum"),
            mean_margin=("boundary_margin", "mean"),
            std_value=("value", "std"),
        )
        .fillna({"std_value": 0.0})
    )
    grouped["failure_rate"] = grouped["failures"] / grouped["runs"]
    grouped["flakiness"] = 2.0 * np.minimum(grouped["failure_rate"], 1.0 - grouped["failure_rate"])
    grouped["suspicion_score"] = (
        0.45 * grouped["failure_rate"]
        + 0.30 * (grouped["anomalies"] / grouped["runs"])
        + 0.20 * grouped["flakiness"]
        + 0.05 * np.maximum(0.0, 0.15 - grouped["mean_margin"]) / 0.15
    ).clip(0, 1)

    suspicious = grouped.sort_values("suspicion_score", ascending=False).head(8)
    top_suspicious = suspicious[
        ["test_name", "signal", "runs", "failures", "anomalies", "failure_rate", "flakiness", "suspicion_score"]
    ].round(4).to_dict(orient="records")

    signal_health = (
        grouped.groupby("signal", as_index=False)
        .agg(runs=("runs", "sum"), failures=("failures", "sum"), anomalies=("anomalies", "sum"))
    )
    signal_health["health_score"] = (
        1.0 - 0.7 * signal_health["failures"] / signal_health["runs"] - 0.3 * signal_health["anomalies"] / signal_health["runs"]
    ).clip(0, 1)
    health_rows = signal_health.round(4).sort_values("health_score").to_dict(orient="records")

    failed = int(df["failed"].sum())
    anomalies = int(df["anomaly"].sum())
    total = len(df)
    recommendations: list[str] = []
    if failed:
        recommendations.append("Prioritize boundary and environmental regressions for signals with repeated range failures.")
    if anomalies:
        recommendations.append("Re-run ML-flagged measurements with controlled temperature and supply voltage to separate DUT faults from bench noise.")
    if any(float(row["flakiness"]) > 0.35 for row in top_suspicious):
        recommendations.append("Quarantine highly flaky tests and collect repeated measurements before treating them as release blockers.")
    if not recommendations:
        recommendations.append("No high-risk behavior detected; continue trend monitoring and increase coverage at specification boundaries.")

    return AnalysisSummary(
        total_measurements=total,
        failed_measurements=failed,
        anomalous_measurements=anomalies,
        pass_rate=round((total - failed) / total, 4),
        top_suspicious_tests=top_suspicious,
        signal_health=health_rows,
        recommendations=recommendations,
    )
