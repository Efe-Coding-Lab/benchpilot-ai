"""Optional MCP server exposing BenchPilot tools to an LLM client.

Install with: pip install -e '.[mcp]'
Run with:     python -m benchpilot_ai.mcp_server
"""
from __future__ import annotations

from .analytics import analyze_runs
from .db import init_db, session_scope
from .maintenance import DatabaseMaintenanceAgent
from .planning import generate_plan

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Install MCP support with: pip install -e '.[mcp]'") from exc

mcp = FastMCP("BenchPilot AI")


@mcp.tool()
def analyze_validation_runs() -> dict:
    """Analyze stored validation measurements for failures, anomalies, and flaky tests."""
    init_db()
    with session_scope() as session:
        return analyze_runs(session).to_dict()


@mcp.tool()
def inspect_validation_database() -> dict:
    """Inspect database health, duplicate data, index coverage, and maintenance suggestions."""
    init_db()
    with session_scope() as session:
        return DatabaseMaintenanceAgent(session).inspect()


@mcp.tool()
def generate_validation_plan(project: str, requirements: list[dict]) -> dict:
    """Generate deterministic risk-ranked validation cases from structured requirements."""
    init_db()
    with session_scope() as session:
        analysis = analyze_runs(session).to_dict()
        cases = generate_plan(session, project, requirements, analysis=analysis)
        return {"count": len(cases), "cases": [case.to_dict() for case in cases]}


if __name__ == "__main__":  # pragma: no cover
    mcp.run()
