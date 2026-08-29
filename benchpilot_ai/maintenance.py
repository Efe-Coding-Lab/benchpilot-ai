from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, func, inspect, select, text
from sqlalchemy.orm import Session

from .models import AgentEvent, TestPlan, TestRun

EXPECTED_INDEXES = {
    "test_runs": {"ix_test_runs_timestamp", "ix_test_runs_test_signal_time", "ix_test_runs_device_time"},
    "test_plans": {"ix_test_plans_requirement_id"},
    "agent_events": {"ix_agent_events_event_type"},
}


def inspect_database(session: Session) -> dict[str, Any]:
    engine = session.get_bind()
    inspector = inspect(engine)
    counts = {
        "test_runs": int(session.scalar(select(func.count(TestRun.id))) or 0),
        "test_plans": int(session.scalar(select(func.count(TestPlan.id))) or 0),
        "agent_events": int(session.scalar(select(func.count(AgentEvent.id))) or 0),
    }
    duplicate_groups = int(
        session.scalar(
            select(func.count()).select_from(
                select(TestRun.run_id, TestRun.test_name, TestRun.signal, TestRun.timestamp)
                .group_by(TestRun.run_id, TestRun.test_name, TestRun.signal, TestRun.timestamp)
                .having(func.count(TestRun.id) > 1)
                .subquery()
            )
        )
        or 0
    )

    missing_indexes: dict[str, list[str]] = {}
    for table, expected in EXPECTED_INDEXES.items():
        if table not in inspector.get_table_names():
            continue
        actual = {idx["name"] for idx in inspector.get_indexes(table)}
        missing = sorted(expected - actual)
        if missing:
            missing_indexes[table] = missing

    oldest = session.scalar(select(func.min(TestRun.timestamp)))
    newest = session.scalar(select(func.max(TestRun.timestamp)))
    suggestions: list[str] = []
    if duplicate_groups:
        suggestions.append(f"Deduplicate {duplicate_groups} repeated measurement key groups before training or KPI calculation.")
    if missing_indexes:
        suggestions.append("Create missing indexes before the measurement history grows; expected indexes are tuned for time-series and per-signal queries.")
    if counts["test_runs"] > 250_000:
        suggestions.append("Consider time-based partitioning in PostgreSQL for test_runs and archive old raw measurements.")
    if not suggestions:
        suggestions.append("Schema health looks good; keep retention and query-plan checks in the CI/operations loop.")

    return {
        "dialect": engine.dialect.name,
        "table_counts": counts,
        "duplicate_measurement_groups": duplicate_groups,
        "missing_indexes": missing_indexes,
        "oldest_measurement": oldest.isoformat() if oldest else None,
        "newest_measurement": newest.isoformat() if newest else None,
        "suggestions": suggestions,
    }


def retention(session: Session, days: int = 180, dry_run: bool = True) -> dict[str, Any]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    count = int(session.scalar(select(func.count(TestRun.id)).where(TestRun.timestamp < cutoff)) or 0)
    if not dry_run and count:
        session.execute(delete(TestRun).where(TestRun.timestamp < cutoff))
        session.flush()
    return {"cutoff": cutoff.isoformat(), "matching_rows": count, "deleted_rows": 0 if dry_run else count, "dry_run": dry_run}


def optimize(session: Session, dry_run: bool = True) -> dict[str, Any]:
    dialect = session.get_bind().dialect.name
    commands = ["ANALYZE test_runs", "ANALYZE test_plans"] if dialect == "postgresql" else ["ANALYZE"]
    if not dry_run:
        for command in commands:
            session.execute(text(command))
    return {"dialect": dialect, "commands": commands, "executed": not dry_run}


class DatabaseMaintenanceAgent:
    """Small operational agent for validation-data housekeeping.

    It is intentionally conservative: inspection and maintenance actions default
    to dry-run so an AI client cannot silently delete historical evidence.
    """

    def __init__(self, session: Session):
        self.session = session

    def inspect(self) -> dict[str, Any]:
        return inspect_database(self.session)

    def retention(self, days: int = 180, apply: bool = False) -> dict[str, Any]:
        return retention(self.session, days=days, dry_run=not apply)

    def optimize(self, apply: bool = False) -> dict[str, Any]:
        return optimize(self.session, dry_run=not apply)

    def run(self, retention_days: int = 180) -> dict[str, Any]:
        return {
            "inspection": self.inspect(),
            "retention_preview": self.retention(days=retention_days, apply=False),
            "optimization_preview": self.optimize(apply=False),
        }
