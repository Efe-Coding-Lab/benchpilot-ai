from __future__ import annotations

from benchpilot_ai.planning import generate_plan


def test_plan_contains_boundary_fault_and_closed_loop_cases(session):
    requirements = [
        {
            "id": "REQ-1",
            "title": "Reference voltage",
            "signal": "vref",
            "lower": 3.2,
            "upper": 3.4,
            "unit": "V",
            "risk": "high",
            "contexts": [{"temperature_c": 125, "supply_v": 3.0}],
            "faults": ["reference drift"],
        }
    ]
    analysis = {
        "top_suspicious_tests": [
            {"test_name": "adc_reference", "signal": "vref", "suspicion_score": 0.7}
        ]
    }
    cases = generate_plan(session, "demo", requirements, analysis=analysis)
    kinds = {case.kind for case in cases}
    assert "boundary" in kinds
    assert "fault-injection" in kinds
    assert "environmental" in kinds
    assert "anomaly-followup" in kinds
    assert cases[0].priority >= cases[-1].priority
