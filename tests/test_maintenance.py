from __future__ import annotations

from benchpilot_ai.maintenance import DatabaseMaintenanceAgent, inspect_database, retention


def test_database_agent_reports_health(session):
    result = inspect_database(session)
    assert result["dialect"] == "sqlite"
    assert "test_runs" in result["table_counts"]
    dry = retention(session, days=7, dry_run=True)
    assert dry["dry_run"] is True
    agent = DatabaseMaintenanceAgent(session)
    preview = agent.run(retention_days=7)
    assert preview["retention_preview"]["dry_run"] is True
    assert preview["optimization_preview"]["executed"] is False
