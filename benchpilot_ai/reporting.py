from __future__ import annotations

import base64
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .planning import PlanCase


def _chart_base64(signal_health: list[dict[str, Any]]) -> str | None:
    if not signal_health:
        return None
    labels = [str(row["signal"]) for row in signal_health]
    scores = [float(row["health_score"]) for row in signal_health]
    fig, ax = plt.subplots(figsize=(8, max(2.8, len(labels) * 0.45)))
    ax.barh(labels, scores)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Health score (1 = best)")
    ax.set_title("Signal health")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=140)
    plt.close(fig)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _mermaid_for_plan(cases: list[PlanCase]) -> str:
    by_kind: dict[str, int] = {}
    for case in cases:
        by_kind[case.kind] = by_kind.get(case.kind, 0) + 1
    lines = ["flowchart LR", '  A[Requirements] --> B[Test-plan generator]']
    for idx, (kind, count) in enumerate(sorted(by_kind.items()), start=1):
        node = f"K{idx}"
        label = kind.replace('"', "'")
        lines.append(f'  B --> {node}["{label}: {count}"]')
        lines.append(f"  {node} --> Z[Execution & measurements]")
    lines.extend(["  Z --> M[ML anomaly detection]", "  M --> R[Automated report]", "  M --> B"])
    return "\n".join(lines)


def generate_report(
    analysis: dict[str, Any],
    plan: list[PlanCase],
    maintenance: dict[str, Any],
    output_dir: str | Path = "reports",
    title: str = "BenchPilot Validation Report",
) -> dict[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    html_path = output / f"validation_report_{stamp}.html"
    md_path = output / f"validation_report_{stamp}.md"
    mermaid_path = output / f"validation_flow_{stamp}.mmd"

    template_dir = Path(__file__).resolve().parent.parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=select_autoescape(["html", "xml"]))
    template = env.get_template("report.html.j2")
    chart = _chart_base64(analysis.get("signal_health", []))
    generated_at = datetime.now(timezone.utc).isoformat()
    html = template.render(
        title=title,
        generated_at=generated_at,
        analysis=analysis,
        plan=[case.to_dict() for case in plan],
        maintenance=maintenance,
        chart_base64=chart,
    )
    html_path.write_text(html, encoding="utf-8")

    md_lines = [
        f"# {title}",
        "",
        f"Generated: `{generated_at}`",
        "",
        "## Executive summary",
        f"- Measurements: **{analysis.get('total_measurements', 0)}**",
        f"- Pass rate: **{analysis.get('pass_rate', 0) * 100:.1f}%**",
        f"- Failures: **{analysis.get('failed_measurements', 0)}**",
        f"- ML anomalies: **{analysis.get('anomalous_measurements', 0)}**",
        f"- Generated test cases: **{len(plan)}**",
        "",
        "## Recommendations",
    ]
    md_lines += [f"- {item}" for item in analysis.get("recommendations", [])]
    md_lines += ["", "## Highest-priority test cases"]
    for case in plan[:12]:
        md_lines += [f"### P{case.priority} — {case.title}", case.rationale, ""]
        md_lines += [f"1. {step}" for step in case.steps]
        md_lines += [f"Expected: {case.expected}", ""]
    md_lines += ["## Database maintenance", "", "```json", json.dumps(maintenance, indent=2), "```", ""]
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    mermaid_path.write_text(_mermaid_for_plan(plan), encoding="utf-8")
    return {"html": str(html_path), "markdown": str(md_path), "mermaid": str(mermaid_path)}
