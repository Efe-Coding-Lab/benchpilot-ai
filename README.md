# BenchPilot AI

**Closed-loop, agentic validation automation for hardware and embedded test benches.**

BenchPilot turns raw lab measurements into a risk-ranked next test plan. It combines deterministic validation rules, **Isolation Forest anomaly detection**, flaky-test scoring, an optional **local LLM** enhancement layer, a **PostgreSQL maintenance agent**, automated HTML/Markdown reporting, Mermaid diagram generation, FastAPI endpoints, and optional **MCP tools**.

> Portfolio idea: instead of building another generic chatbot, this project applies AI to a real validation-engineering workflow: **measure → analyze → plan → maintain → report → feed anomalies back into the next plan**.

## Why this project is relevant to validation / GenAI roles

| Role need | Where BenchPilot demonstrates it |
|---|---|
| Automate test measurements and data processing | CSV/JSON ingestion, range evaluation, analytics pipeline |
| AI/ML | `IsolationForest` anomaly detection + flaky-test scoring |
| GenAI / prompt engineering | Structured prompt for lab-ready test-case enhancement; local Ollama adapter with deterministic fallback |
| Agents | `ValidationAgent` orchestrates analytics → plan generation → DB maintenance → report generation |
| Automated tables, diagrams, reports | HTML + Markdown reports, charts, Mermaid flow diagrams |
| PostgreSQL / efficient SQL | SQLAlchemy schema, composite indexes, duplicate checks, retention and ANALYZE maintenance actions |
| SQL query design | `sql/analysis_queries.sql` contains failure-hotspot, flaky-test, and `EXPLAIN (ANALYZE, BUFFERS)` examples |
| Automated test-plan generation | Boundary, negative, environmental, fault-injection, and anomaly-driven follow-up cases |
| MCP tools | Optional MCP server exposes analysis, DB inspection, and plan-generation tools |
| Python and C | Python application plus a small C measurement producer example |
| Debugging / code review quality | Pytest suite, CI workflow, typed modules, deterministic fallback behavior |

## Architecture

```mermaid
flowchart LR
    A[Bench / C producer / CSV] --> B[Ingestion]
    B --> C[(SQLite or PostgreSQL)]
    C --> D[Range rules + Isolation Forest]
    D --> E[Flaky-test & suspicion scoring]
    E --> F[Risk-ranked test-plan generator]
    F --> G[Optional local LLM enhancement]
    E --> H[DB maintenance agent]
    F --> I[HTML / Markdown / Mermaid report]
    D --> F
    J[MCP client] --> K[MCP tools]
    K --> D
    K --> F
    K --> H
```

## Quick start — zero external services

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\\Scripts\\activate
pip install -e '.[dev]'

python scripts/generate_demo_data.py
benchpilot init-db
benchpilot ingest data/demo_measurements.csv
benchpilot cycle examples/requirements.yaml --no-llm
```

The last command prints paths to an HTML report, Markdown report, and Mermaid diagram in `reports/`.

A committed example is available in `docs/sample_validation_report.html` and `docs/sample_validation_report.md` so reviewers can inspect output without running the project first.

Run the test suite:

```bash
pytest
```

## API

```bash
uvicorn benchpilot_ai.api:app --reload
```

Open the generated API docs at `http://127.0.0.1:8000/docs`.

Useful endpoints:

- `POST /runs` — ingest structured measurements
- `GET /analysis` — failures, ML anomalies, signal health, flaky-test scores
- `POST /plans` — generate risk-ranked validation cases
- `GET /maintenance` — inspect DB health and index coverage
- `POST /maintenance/retention?days=180&apply=false` — retention dry-run / apply
- `POST /maintenance/optimize?apply=false` — show or execute DB ANALYZE actions
- `POST /agent/cycle` — run the complete agentic validation loop

## PostgreSQL mode

Use Docker Compose:

```bash
docker compose up --build
```

Or point a local process to PostgreSQL:

```bash
export DATABASE_URL='postgresql+psycopg://benchpilot:benchpilot@localhost:5432/benchpilot'
pip install -e '.[postgres]'
benchpilot init-db
```

The schema includes indexes for common validation queries: time history, `(test_name, signal, timestamp)`, and `(device, timestamp)`.

## Optional local GenAI enhancement

BenchPilot works without an LLM. This is deliberate: the validation rules remain reproducible and testable. If you run a local Ollama model, the planner can add extra lab-ready cases while preserving the deterministic baseline.

```bash
export BENCHPILOT_LLM=ollama
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama3.1:8b
benchpilot cycle examples/requirements.yaml
```

The prompt is in `benchpilot_ai/prompts.py`. It requests JSON-only output and explicitly forbids widening requirement limits. If the model is unavailable or returns bad JSON, the pipeline safely falls back to deterministic cases.

## MCP server

```bash
pip install -e '.[mcp]'
python -m benchpilot_ai.mcp_server
```

Exposed tools:

- `analyze_validation_runs`
- `inspect_validation_database`
- `generate_validation_plan`

This makes the same audited validation functions callable by an MCP-capable AI client instead of hiding business logic inside prompts.

## C measurement producer

The `examples/c_probe/measurement_probe.c` example mimics a small embedded-side data producer:

```bash
gcc -O2 examples/c_probe/measurement_probe.c -o measurement_probe
./measurement_probe > data/c_probe_measurements.csv
benchpilot ingest data/c_probe_measurements.csv
```

## What makes the project different

Most LLM portfolio projects stop at “chat with data.” BenchPilot has a **closed validation loop**. Historical measurements affect the next planned tests: if the model/rules identify an unstable or anomalous test, the planner creates a targeted repeatability and environmental follow-up case. That makes the AI useful to an engineering workflow rather than decorative.

## Suggested GitHub screenshots

1. Swagger UI showing `/agent/cycle` and `/maintenance`.
2. The generated HTML report with signal-health chart and suspicious-test table.
3. The Mermaid architecture diagram from this README.
4. A terminal screenshot of `pytest` passing.
5. A PostgreSQL run via `docker compose up`.

## Interview talking points

- **Why Isolation Forest?** It handles multidimensional outlier detection without needing labeled failures; range checks remain the source of truth for specification compliance.
- **Why deterministic + LLM?** Safety and reproducibility. The LLM may suggest coverage, but it cannot replace hard limits or make pass/fail decisions.
- **Why PostgreSQL maintenance?** Validation data grows quickly. Index health, duplicate detection, retention, and query statistics are part of making an automation system operationally useful.
- **Why MCP?** It exposes bounded engineering tools to AI clients while keeping SQL and analytics code deterministic and reviewable.
- **How would this connect to real benches?** Replace CSV input with a message queue, REST client, CAN/LIN/serial adapter, or test framework exporter; the analysis and persistence contracts stay the same.

## Repository layout

```text
benchpilot_ai/
  agent.py          # orchestration
  analytics.py      # ML + quality metrics
  planning.py       # deterministic + optional LLM test planning
  maintenance.py    # DB health/retention/optimization agent
  reporting.py      # automated HTML/Markdown/diagram artifacts
  api.py            # FastAPI
  mcp_server.py     # optional MCP tools
examples/
  requirements.yaml
  c_probe/
scripts/
  generate_demo_data.py
tests/
```

## Roadmap ideas

- Add CAN/LIN/serial measurement adapters.
- Use PostgreSQL partitioning for high-volume time-series data.
- Add human approval before LLM-generated cases enter a release test plan.
- Compare anomaly distributions across silicon revisions.
- Export results to JUnit XML for CI systems.

## License

MIT
