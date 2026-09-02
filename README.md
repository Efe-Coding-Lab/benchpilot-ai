# BenchPilot AI

BenchPilot is a prototype validation workflow for processing test measurements, identifying suspicious results, and generating follow-up test cases.

It combines deterministic validation rules with anomaly detection, test-history analysis, optional local LLM-assisted planning, PostgreSQL maintenance utilities, and automated reporting.

The basic workflow is:

**measurements → analysis → test planning → reporting → follow-up tests**

## Overview

BenchPilot accepts structured measurement data from CSV or JSON and stores the results in SQLite or PostgreSQL.

The analysis layer evaluates measurements against configured limits and uses Isolation Forest to flag unusual observations. Historical results are also used to identify tests that appear unstable or flaky.

These results are then passed to the planner, which generates follow-up validation cases based on failures, anomalies, and configured requirements.

An optional local LLM can add additional test-case suggestions, but the deterministic test plan remains available if the model is disabled, unavailable, or returns invalid output.

## Architecture

```mermaid
flowchart LR
    A[Bench / C producer / CSV] --> B[Ingestion]
    B --> C[(SQLite or PostgreSQL)]
    C --> D[Range checks + Isolation Forest]
    D --> E[Flaky-test & suspicion scoring]
    E --> F[Test-plan generator]
    F --> G[Optional local LLM]
    E --> H[Database maintenance]
    F --> I[HTML / Markdown / Mermaid reports]
    D --> F
    J[MCP client] --> K[MCP tools]
    K --> D
    K --> F
    K --> H
```

## Features

- CSV and JSON measurement ingestion
- configurable measurement limits
- Isolation Forest anomaly detection
- flaky-test and signal-health analysis
- risk-ranked test-plan generation
- boundary and negative test generation
- environmental and fault-injection test cases
- anomaly-driven follow-up tests
- SQLite and PostgreSQL support
- database health and retention checks
- HTML and Markdown reports
- Mermaid validation-flow diagrams
- FastAPI interface
- optional MCP tools
- optional local Ollama integration
- Pytest test suite

## Quick start

The default setup uses SQLite and does not require any external services.

```bash
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate

pip install -e '.[dev]'

python scripts/generate_demo_data.py
benchpilot init-db
benchpilot ingest data/demo_measurements.csv
benchpilot cycle examples/requirements.yaml --no-llm
```

Generated reports are written to:

```text
reports/
```

Example outputs are also included in:

```text
docs/sample_validation_report.html
docs/sample_validation_report.md
```

Run the tests with:

```bash
pytest
```

## Validation cycle

A normal cycle consists of four main stages.

### 1. Measurement analysis

Measurements are evaluated against configured requirements.

The analytics layer also applies Isolation Forest to identify observations that may be unusual even when they do not directly violate a configured limit.

Historical test results are used to calculate additional indicators such as flaky-test and signal-health scores.

### 2. Test-plan generation

The planner generates follow-up cases from the analysis results.

Current case types include:

- boundary tests
- negative tests
- environmental tests
- fault-injection tests
- anomaly-driven repeatability tests

Cases are ranked so that failures and suspicious measurements can influence which tests should be investigated next.

### 3. Database maintenance

BenchPilot includes database checks for:

- duplicate records
- retention candidates
- index coverage
- PostgreSQL `ANALYZE` actions

The repository also contains example analysis queries using:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

### 4. Reporting

Each cycle can generate:

- HTML reports
- Markdown reports
- summary tables
- Mermaid diagrams

The reports contain the measurement analysis and the generated follow-up test plan.

## API

Start the API with:

```bash
uvicorn benchpilot_ai.api:app --reload
```

FastAPI documentation is available at:

```text
http://127.0.0.1:8000/docs
```

Main endpoints:

- `POST /runs` — ingest measurement data
- `GET /analysis` — analyze failures, anomalies, and test history
- `POST /plans` — generate a validation plan
- `GET /maintenance` — inspect database health
- `POST /maintenance/retention?days=180&apply=false` — retention check
- `POST /maintenance/optimize?apply=false` — database optimization actions
- `POST /agent/cycle` — run the complete validation cycle

## PostgreSQL

The default configuration can run with SQLite.

For PostgreSQL, Docker Compose can be used:

```bash
docker compose up --build
```

A local PostgreSQL instance can also be configured directly:

```bash
export DATABASE_URL='postgresql+psycopg://benchpilot:benchpilot@localhost:5432/benchpilot'

pip install -e '.[postgres]'
benchpilot init-db
```

The schema includes indexes for common validation queries, including:

- measurement history by time
- `(test_name, signal, timestamp)`
- `(device, timestamp)`

Additional SQL examples are available in:

```text
sql/analysis_queries.sql
```

## Optional local LLM

The validation pipeline does not require an LLM.

The deterministic planner always produces the baseline test plan. A local model can optionally suggest additional cases based on the same analysis results.

Example configuration with Ollama:

```bash
export BENCHPILOT_LLM=ollama
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama3.1:8b

benchpilot cycle examples/requirements.yaml
```

The prompt implementation is located in:

```text
benchpilot_ai/prompts.py
```

The model is asked to return structured JSON output and is not allowed to modify configured requirement limits.

If the model cannot be reached or its response cannot be parsed, BenchPilot continues with the deterministic test cases.

## MCP tools

BenchPilot can optionally expose several functions through MCP.

Install the MCP dependencies:

```bash
pip install -e '.[mcp]'
```

Start the server:

```bash
python -m benchpilot_ai.mcp_server
```

Available tools:

- `analyze_validation_runs`
- `inspect_validation_database`
- `generate_validation_plan`

These tools call the same analysis and planning functions used by the normal application.

## C measurement example

The repository includes a small C program that produces measurement data in the same format expected by BenchPilot.

```bash
gcc -O2 examples/c_probe/measurement_probe.c -o measurement_probe

./measurement_probe > data/c_probe_measurements.csv

benchpilot ingest data/c_probe_measurements.csv
```

The example is located at:

```text
examples/c_probe/measurement_probe.c
```

## Repository layout

```text
benchpilot_ai/
  agent.py
  analytics.py
  planning.py
  maintenance.py
  reporting.py
  api.py
  mcp_server.py
  prompts.py

examples/
  requirements.yaml
  c_probe/

scripts/
  generate_demo_data.py

sql/
  analysis_queries.sql

tests/

docs/
  sample_validation_report.html
  sample_validation_report.md
```

## Design notes

A few design decisions are intentional:

**Deterministic validation comes first.**  
Configured limits and rule-based test generation do not depend on an LLM.

**ML is used as an additional signal.**  
Anomaly detection can identify measurements worth investigating without replacing explicit engineering requirements.

**LLM output is optional.**  
The system continues to work when no model is configured.

**Generated test cases are traceable to analysis results.**  
Failures, anomalies, and unstable tests can produce targeted follow-up cases in the next plan.

**Database operations can be inspected before they are applied.**  
Retention and optimization operations support dry-run behavior.

## Current scope

BenchPilot currently focuses on structured CSV/JSON measurement workflows and simulated/example validation data.

Possible next steps include:

- CAN, LIN, or serial measurement adapters
- PostgreSQL partitioning for larger time-series datasets
- human approval for generated test cases
- comparison of anomaly distributions across hardware revisions
- JUnit XML export for CI systems
