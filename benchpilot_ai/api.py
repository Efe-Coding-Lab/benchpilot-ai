from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .agent import ValidationAgent
from .analytics import analyze_runs
from .db import init_db, session_scope
from .ingest import add_runs
from .maintenance import inspect_database, optimize, retention
from .planning import generate_plan
from .schemas import AgentCycleRequest, JsonResponse, PlanRequest, RunInput

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="BenchPilot AI",
    version="0.1.0",
    description="Agentic hardware-validation automation with ML analytics, test planning, database maintenance, and reporting.",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/runs", response_model=JsonResponse)
def ingest_runs(rows: list[RunInput]) -> JsonResponse:
    if not rows:
        raise HTTPException(status_code=400, detail="At least one measurement is required")
    with session_scope() as session:
        inserted = add_runs(session, rows)
    return JsonResponse(data={"inserted": inserted})


@app.get("/analysis", response_model=JsonResponse)
def analysis() -> JsonResponse:
    with session_scope() as session:
        result = analyze_runs(session).to_dict()
    return JsonResponse(data=result)


@app.post("/plans", response_model=JsonResponse)
def create_plan(request: PlanRequest) -> JsonResponse:
    with session_scope() as session:
        analysis_result = analyze_runs(session).to_dict() if request.include_anomaly_followups else None
        cases = generate_plan(
            session,
            request.project,
            [r.model_dump() for r in request.requirements],
            analysis=analysis_result,
        )
    return JsonResponse(data={"count": len(cases), "cases": [case.to_dict() for case in cases]})


@app.get("/maintenance", response_model=JsonResponse)
def maintenance() -> JsonResponse:
    with session_scope() as session:
        result = inspect_database(session)
    return JsonResponse(data=result)


@app.post("/maintenance/retention", response_model=JsonResponse)
def maintenance_retention(days: int = 180, apply: bool = False) -> JsonResponse:
    with session_scope() as session:
        result = retention(session, days=days, dry_run=not apply)
    return JsonResponse(data=result)


@app.post("/maintenance/optimize", response_model=JsonResponse)
def maintenance_optimize(apply: bool = False) -> JsonResponse:
    with session_scope() as session:
        result = optimize(session, dry_run=not apply)
    return JsonResponse(data=result)


@app.post("/agent/cycle", response_model=JsonResponse)
def agent_cycle(request: AgentCycleRequest) -> JsonResponse:
    with session_scope() as session:
        result = ValidationAgent(session).run_cycle(
            project=request.project,
            requirements=[r.model_dump() for r in request.requirements],
            report_title=request.report_title,
        )
    return JsonResponse(data=result)
