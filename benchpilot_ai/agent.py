from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from .analytics import analyze_runs
from .llm import provider_from_settings
from .maintenance import DatabaseMaintenanceAgent
from .models import AgentEvent
from .planning import generate_plan
from .reporting import generate_report


class ValidationAgent:
    """Orchestrates a closed-loop validation cycle using deterministic tools plus optional GenAI enhancement."""

    def __init__(self, session: Session):
        self.session = session

    def _event(self, event_type: str, message: str, payload: dict[str, Any]) -> None:
        self.session.add(AgentEvent(event_type=event_type, message=message, payload_json=json.dumps(payload, default=str)))
        self.session.flush()

    def run_cycle(
        self,
        project: str,
        requirements: list[dict[str, Any]],
        report_title: str = "BenchPilot Validation Report",
        output_dir: str | Path = "reports",
        use_llm: bool = True,
    ) -> dict[str, Any]:
        analysis = analyze_runs(self.session).to_dict()
        self._event("analysis", "Measurement analytics completed", analysis)

        provider = provider_from_settings() if use_llm else None
        plan = generate_plan(self.session, project, requirements, analysis=analysis, provider=provider)
        self._event("planning", "Risk-ranked test plan generated", {"count": len(plan), "llm_enabled": provider is not None})

        maintenance = DatabaseMaintenanceAgent(self.session).inspect()
        self._event("maintenance", "Database health inspection completed", maintenance)

        paths = generate_report(analysis, plan, maintenance, output_dir=output_dir, title=report_title)
        self._event("report", "Automated report artifacts generated", paths)

        return {
            "analysis": analysis,
            "plan": [case.to_dict() for case in plan],
            "maintenance": maintenance,
            "artifacts": paths,
        }
