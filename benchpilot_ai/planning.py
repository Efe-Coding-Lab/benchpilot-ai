from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from .llm import LLMProvider
from .models import TestPlan
from .prompts import plan_enhancement_prompt

RISK_PRIORITY = {"critical": 100, "high": 80, "medium": 55, "low": 30}


@dataclass
class PlanCase:
    requirement_id: str
    title: str
    priority: int
    kind: str
    rationale: str
    steps: list[str]
    expected: str
    source: str = "deterministic"

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "title": self.title,
            "priority": self.priority,
            "kind": self.kind,
            "rationale": self.rationale,
            "steps": self.steps,
            "expected": self.expected,
            "source": self.source,
        }


def _priority(risk: str, bonus: int = 0) -> int:
    return min(100, RISK_PRIORITY.get(risk.lower(), 55) + bonus)


def _baseline_cases(requirement: dict[str, Any]) -> list[PlanCase]:
    rid = requirement["id"]
    title = requirement["title"]
    signal = requirement["signal"]
    lower = float(requirement["lower"])
    upper = float(requirement["upper"])
    unit = requirement.get("unit", "")
    risk = str(requirement.get("risk", "medium"))
    span = upper - lower
    midpoint = lower + span / 2.0
    eps = span * 0.02 if span else max(abs(lower), 1.0) * 0.02

    cases = [
        PlanCase(
            rid,
            f"{title} — nominal operating point",
            _priority(risk),
            "nominal",
            "Establish a clean reference result before stressing the requirement.",
            [f"Configure the DUT and bench for {signal} measurement.", f"Drive the target near {midpoint:.4g} {unit}.", "Capture at least 20 repeated samples and timestamps."],
            f"Every stable sample remains between {lower:g} and {upper:g} {unit}.",
        ),
        PlanCase(
            rid,
            f"{title} — lower specification boundary",
            _priority(risk, 8),
            "boundary",
            "Boundary-value testing finds quantization, calibration, and comparator errors that nominal tests miss.",
            [f"Sweep {signal} toward the lower limit from inside the valid range.", f"Hold at {lower + eps:.4g} {unit}, then at {lower:.4g} {unit}.", "Repeat across three independent runs."],
            f"Values at or above {lower:g} {unit} pass; measurement uncertainty is recorded.",
        ),
        PlanCase(
            rid,
            f"{title} — upper specification boundary",
            _priority(risk, 8),
            "boundary",
            "Upper-edge behavior can reveal saturation, thermal drift, or arithmetic overflow.",
            [f"Sweep {signal} toward the upper limit from inside the valid range.", f"Hold at {upper - eps:.4g} {unit}, then at {upper:.4g} {unit}.", "Repeat across three independent runs."],
            f"Values at or below {upper:g} {unit} pass; measurement uncertainty is recorded.",
        ),
        PlanCase(
            rid,
            f"{title} — out-of-range fault detection",
            _priority(risk, 12),
            "negative",
            "A validation flow should verify that invalid behavior is detected rather than silently accepted.",
            [f"Inject one sample below {lower:g} {unit} and one above {upper:g} {unit} using a safe simulator or mocked source.", "Run the same parser and validation pipeline used for normal data.", "Confirm failure classification and report traceability."],
            "Both injected violations are marked FAIL and appear in the generated report.",
        ),
    ]

    for idx, context in enumerate(requirement.get("contexts", []), start=1):
        temp = context.get("temperature_c")
        supply = context.get("supply_v")
        context_bits = []
        if temp is not None:
            context_bits.append(f"temperature={temp:g} °C")
        if supply is not None:
            context_bits.append(f"supply={supply:g} V")
        desc = ", ".join(context_bits) or f"corner {idx}"
        cases.append(
            PlanCase(
                rid,
                f"{title} — environmental corner {idx}",
                _priority(risk, 10),
                "environmental",
                f"Validate the requirement under the specified operating context ({desc}).",
                [f"Condition the setup to {desc}.", "Wait for stabilization and record the condition.", f"Repeat nominal and boundary checks for {signal}."],
                f"{signal} remains between {lower:g} and {upper:g} {unit} at {desc}.",
            )
        )

    for idx, fault in enumerate(requirement.get("faults", []), start=1):
        cases.append(
            PlanCase(
                rid,
                f"{title} — fault injection {idx}",
                _priority(risk, 15),
                "fault-injection",
                f"Exercise diagnostic coverage for the declared fault: {fault}.",
                [f"Inject or simulate fault: {fault}.", "Capture DUT response, timing, and recovery behavior.", "Remove the fault and verify the system returns to the baseline state."],
                "The fault is detected or safely contained, with deterministic recovery and traceable evidence.",
            )
        )

    return cases


def _safe_llm_enhancement(project: str, requirement: dict[str, Any], cases: list[PlanCase], provider: LLMProvider | None) -> list[PlanCase]:
    if provider is None:
        return cases
    prompt = plan_enhancement_prompt(project, requirement, [case.to_dict() for case in cases])
    try:
        raw = provider.generate(prompt)
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            parsed = parsed.get("cases", parsed.get("tests", []))
        if not isinstance(parsed, list) or not parsed:
            return cases
        enhancements: list[PlanCase] = []
        for idx, item in enumerate(parsed[:6]):
            if not isinstance(item, dict):
                continue
            steps = item.get("steps")
            if not isinstance(steps, list) or not steps:
                continue
            enhancements.append(
                PlanCase(
                    requirement_id=requirement["id"],
                    title=str(item.get("title", f"LLM-enhanced case {idx + 1}")),
                    priority=_priority(str(requirement.get("risk", "medium")), 7),
                    kind="llm-enhanced",
                    rationale=str(item.get("rationale", "LLM suggested additional coverage.")),
                    steps=[str(step) for step in steps],
                    expected=str(item.get("expected", "Requirement remains satisfied and evidence is recorded.")),
                    source="llm",
                )
            )
        return cases + enhancements
    except Exception:
        return cases


def generate_plan(
    session: Session,
    project: str,
    requirements: list[dict[str, Any]],
    analysis: dict[str, Any] | None = None,
    provider: LLMProvider | None = None,
) -> list[PlanCase]:
    cases: list[PlanCase] = []
    for requirement in requirements:
        baseline = _baseline_cases(requirement)
        cases.extend(_safe_llm_enhancement(project, requirement, baseline, provider))

    if analysis:
        for item in analysis.get("top_suspicious_tests", [])[:4]:
            score = float(item.get("suspicion_score", 0.0))
            failures = int(item.get("failures", 0))
            anomalies = int(item.get("anomalies", 0))
            if score < 0.04 and failures < 2 and anomalies < 3:
                continue
            cases.append(
                PlanCase(
                    requirement_id=f"OBSERVED:{item['test_name']}",
                    title=f"Closed-loop follow-up — {item['test_name']} / {item['signal']}",
                    priority=min(100, 65 + int(score * 30)),
                    kind="anomaly-followup",
                    rationale="Generated from observed failures/anomalies so the next validation cycle targets real bench behavior.",
                    steps=[
                        "Repeat the suspicious test for 30 iterations with identical stimulus.",
                        "Repeat at low, nominal, and high declared environmental contexts.",
                        "Compare value distribution, duration, and anomaly score against the previous run.",
                        "If the issue reproduces, isolate bench, DUT, and software variables one at a time.",
                    ],
                    expected="The behavior becomes reproducible enough to classify as DUT defect, bench artifact, or flaky test.",
                    source="closed-loop",
                )
            )

    cases.sort(key=lambda c: (-c.priority, c.requirement_id, c.title))
    for case in cases:
        session.add(
            TestPlan(
                requirement_id=case.requirement_id,
                title=case.title,
                priority=case.priority,
                kind=case.kind,
                rationale=case.rationale,
                steps_json=json.dumps(case.steps),
                expected=case.expected,
                source=case.source,
            )
        )
    session.flush()
    return cases
