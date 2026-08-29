from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import TestRun
from .schemas import RunInput

REQUIRED_COLUMNS = {
    "run_id",
    "timestamp",
    "test_name",
    "signal",
    "value",
    "lower_bound",
    "upper_bound",
}


def _to_utc(value: datetime | str) -> datetime:
    dt = pd.to_datetime(value, utc=True).to_pydatetime()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def add_runs(session: Session, rows: list[RunInput]) -> int:
    inserted = 0
    for row in rows:
        status = "PASS" if row.lower_bound <= row.value <= row.upper_bound else "FAIL"
        session.add(
            TestRun(
                run_id=row.run_id,
                timestamp=_to_utc(row.timestamp),
                bench=row.bench,
                device=row.device,
                test_name=row.test_name,
                signal=row.signal,
                value=row.value,
                lower_bound=row.lower_bound,
                upper_bound=row.upper_bound,
                duration_ms=row.duration_ms,
                temperature_c=row.temperature_c,
                supply_v=row.supply_v,
                computed_status=status,
            )
        )
        inserted += 1
    session.flush()
    return inserted


def ingest_csv(session: Session, path: str | Path) -> int:
    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {sorted(missing)}")

    defaults = {
        "bench": "bench-1",
        "device": "dut-unknown",
        "duration_ms": 0.0,
        "temperature_c": 25.0,
        "supply_v": 3.3,
    }
    for col, default in defaults.items():
        if col not in frame.columns:
            frame[col] = default

    rows = [RunInput(**record) for record in frame.to_dict(orient="records")]
    return add_runs(session, rows)


def fetch_runs(session: Session, limit: int | None = None) -> list[TestRun]:
    stmt = select(TestRun).order_by(TestRun.timestamp.asc())
    if limit:
        stmt = stmt.limit(limit)
    return list(session.scalars(stmt))
