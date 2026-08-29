.PHONY: install test demo api docker
install:
	python -m pip install -e '.[dev]'

test:
	pytest

demo:
	python scripts/generate_demo_data.py
	benchpilot init-db
	benchpilot ingest data/demo_measurements.csv
	benchpilot cycle examples/requirements.yaml --no-llm

api:
	uvicorn benchpilot_ai.api:app --reload

docker:
	docker compose up --build
