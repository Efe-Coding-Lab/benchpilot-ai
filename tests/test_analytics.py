from __future__ import annotations

from datetime import datetime, timedelta, timezone

from benchpilot_ai.analytics import analyze_runs
from benchpilot_ai.ingest import add_runs
from benchpilot_ai.schemas import RunInput


def test_range_failures_and_ml_anomaly_pipeline(session):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows = []
    for i in range(30):
        value = 3.3 + (i % 5 - 2) * 0.005
        if i == 17:
            value = 3.05
        rows.append(
            RunInput(
                run_id=f"R{i}",
                timestamp=start + timedelta(minutes=i),
                test_name="adc_reference",
                signal="vref",
                value=value,
                lower_bound=3.2,
                upper_bound=3.4,
                duration_ms=10 if i != 22 else 90,
                temperature_c=25,
                supply_v=3.3,
            )
        )
    add_runs(session, rows)
    result = analyze_runs(session)
    assert result.total_measurements == 30
    assert result.failed_measurements == 1
    assert result.pass_rate < 1.0
    assert result.anomalous_measurements >= 1
    assert result.top_suspicious_tests[0]["test_name"] == "adc_reference"
