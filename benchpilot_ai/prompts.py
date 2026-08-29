from __future__ import annotations

import json
from typing import Any


def plan_enhancement_prompt(project: str, requirement: dict[str, Any], baseline_cases: list[dict[str, Any]]) -> str:
    return f"""You are a senior semiconductor validation engineer.
Improve the baseline test cases for project {project!r} without changing the requirement limits.
Focus on boundary conditions, environmental corners, reproducibility, fault isolation, and concise lab-ready steps.
Return ONLY a JSON array. Each item must contain: title, rationale, steps (array of strings), expected.
Never invent a wider safe operating range than the supplied lower/upper limits.

Requirement:
{json.dumps(requirement, indent=2)}

Baseline cases:
{json.dumps(baseline_cases, indent=2)}
"""
