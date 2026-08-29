FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY benchpilot_ai ./benchpilot_ai
COPY templates ./templates
RUN pip install --no-cache-dir .[postgres]
ENV DATABASE_URL=postgresql+psycopg://benchpilot:benchpilot@db:5432/benchpilot
EXPOSE 8000
CMD ["uvicorn", "benchpilot_ai.api:app", "--host", "0.0.0.0", "--port", "8000"]
