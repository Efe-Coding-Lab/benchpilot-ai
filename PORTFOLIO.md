# Portfolio / Application Notes

## Suggested GitHub repository description

> Agentic semiconductor validation automation: ML anomaly detection, risk-based LLM test-plan generation, PostgreSQL maintenance, MCP tools, FastAPI, and automated reports.

## Suggested CV bullets

- Built **BenchPilot AI**, a closed-loop validation platform that ingests hardware test measurements, performs specification checks and **Isolation Forest anomaly detection**, and generates risk-ranked follow-up tests from observed failures.
- Implemented an agentic workflow for **automated test-plan generation, HTML/Markdown reporting, Mermaid diagrams, PostgreSQL health/retention checks, and SQL index-aware analytics**, with deterministic fallbacks for reproducibility.
- Exposed validation functions through **FastAPI and MCP tools**, added optional local-LLM prompt engineering for lab-ready test cases, and demonstrated C-to-Python measurement ingestion with CI-tested code.

## 60-second interview explanation

BenchPilot is meant for a validation team rather than as a generic chatbot. A test bench produces timestamped measurements. BenchPilot stores them, evaluates hard specification limits, then uses an Isolation Forest to find unusual multi-dimensional behavior involving measured value, execution time, temperature, and supply voltage. It scores flaky or suspicious tests and feeds those observations into the next test-plan generation cycle. The planner always creates deterministic boundary, negative, environmental, and fault-injection tests; an optional local LLM can add extra lab-ready cases, but it never decides pass/fail or changes requirement limits. A maintenance agent checks the PostgreSQL data layer, and the system automatically produces HTML, Markdown, and Mermaid report artifacts. The same engineering tools are available over FastAPI and MCP.

## Screenshots to add to the GitHub README

1. Generated HTML report showing pass rate, anomaly count, and signal-health chart.
2. `/docs` Swagger page with `/agent/cycle`, `/plans`, and `/maintenance`.
3. Mermaid architecture diagram.
4. Terminal output from `pytest`.
5. Docker Compose running the API and PostgreSQL.

## Before publishing

- Replace `Your Name` in `pyproject.toml`.
- Add your GitHub profile/repository link to the README.
- Run `pytest` and the demo once on your machine.
- Commit one screenshot of the generated report under `docs/images/`.
- Keep generated databases and routine reports out of Git; `.gitignore` already handles them.
