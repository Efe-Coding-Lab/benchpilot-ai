from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from .agent import ValidationAgent
from .analytics import analyze_runs
from .db import init_db, session_scope
from .ingest import ingest_csv
from .maintenance import inspect_database, optimize, retention
from .planning import generate_plan


def _load_requirements(path: str) -> tuple[str, list[dict]]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return str(payload.get("project", "validation-project")), list(payload.get("requirements", []))


def main() -> None:
    parser = argparse.ArgumentParser(prog="benchpilot", description="BenchPilot AI validation automation")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db")

    ingest = sub.add_parser("ingest")
    ingest.add_argument("csv")

    sub.add_parser("analyze")

    plan = sub.add_parser("plan")
    plan.add_argument("requirements")

    cycle = sub.add_parser("cycle")
    cycle.add_argument("requirements")
    cycle.add_argument("--report-title", default="BenchPilot Validation Report")
    cycle.add_argument("--output-dir", default="reports")
    cycle.add_argument("--no-llm", action="store_true")

    retention_cmd = sub.add_parser("retention")
    retention_cmd.add_argument("--days", type=int, default=180)
    retention_cmd.add_argument("--apply", action="store_true")

    optimize_cmd = sub.add_parser("optimize")
    optimize_cmd.add_argument("--apply", action="store_true")

    sub.add_parser("db-health")
    args = parser.parse_args()
    init_db()

    if args.command == "init-db":
        print("Database initialized.")
        return

    with session_scope() as session:
        if args.command == "ingest":
            print(json.dumps({"inserted": ingest_csv(session, args.csv)}, indent=2))
        elif args.command == "analyze":
            print(json.dumps(analyze_runs(session).to_dict(), indent=2))
        elif args.command == "plan":
            project, requirements = _load_requirements(args.requirements)
            analysis = analyze_runs(session).to_dict()
            cases = generate_plan(session, project, requirements, analysis=analysis)
            print(json.dumps({"count": len(cases), "cases": [case.to_dict() for case in cases]}, indent=2))
        elif args.command == "cycle":
            project, requirements = _load_requirements(args.requirements)
            result = ValidationAgent(session).run_cycle(
                project,
                requirements,
                report_title=args.report_title,
                output_dir=args.output_dir,
                use_llm=not args.no_llm,
            )
            print(json.dumps(result, indent=2))
        elif args.command == "retention":
            print(json.dumps(retention(session, days=args.days, dry_run=not args.apply), indent=2))
        elif args.command == "optimize":
            print(json.dumps(optimize(session, dry_run=not args.apply), indent=2))
        elif args.command == "db-health":
            print(json.dumps(inspect_database(session), indent=2))


if __name__ == "__main__":
    main()
