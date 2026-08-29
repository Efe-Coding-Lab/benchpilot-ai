from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RunInput(BaseModel):
    run_id: str
    timestamp: datetime
    bench: str = "bench-1"
    device: str = "dut-unknown"
    test_name: str
    signal: str
    value: float
    lower_bound: float
    upper_bound: float
    duration_ms: float = 0.0
    temperature_c: float = 25.0
    supply_v: float = 3.3


class RequirementInput(BaseModel):
    id: str
    title: str
    signal: str
    lower: float
    upper: float
    unit: str = ""
    risk: str = "medium"
    contexts: list[dict[str, float]] = Field(default_factory=list)
    faults: list[str] = Field(default_factory=list)


class PlanRequest(BaseModel):
    project: str = "validation-project"
    requirements: list[RequirementInput]
    include_anomaly_followups: bool = True


class AgentCycleRequest(PlanRequest):
    report_title: str = "BenchPilot Validation Report"


class JsonResponse(BaseModel):
    ok: bool = True
    data: Any
