# The Agentic GitHub Employee Backend

Production-grade FastAPI backend for a Clean Architecture multi-agent system.
The current MVP exposes a GitHub issue webhook, runs a LangGraph workflow with
Product Manager, Developer, and Reviewer personas, and returns the synchronized
agent state with review status, revision count, execution trace, token telemetry,
and estimated cost.

## Architecture

```text
src/
  domain/          Pure Pydantic models and domain schemas
  application/     LangGraph orchestration and self-correction workflow
  infrastructure/  Sandbox runner port and MVP mock implementation
  interface/       FastAPI web interface
```

Workflow:

```text
GitHub Issue
    |
    v
Product Manager -> Developer -> Reviewer
                         ^        |
                         |        v
                    Self-correct  END
```

The reviewer routes back to the developer when changes are rejected. A circuit
breaker stops the loop after 5 revisions and marks the run as failed.

## Requirements

- Python 3.12+
- UV

Install UV if it is not already available:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Install

From this folder:

```bash
uv sync
```

## Run The API

```bash
uv run uvicorn src.interface.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive docs:

```text
http://127.0.0.1:8000/docs
```

## Test The Webhook

```bash
curl -X POST http://127.0.0.1:8000/webhook/issue \
  -H "Content-Type: application/json" \
  -d '{
    "issue_id": 1,
    "title": "Fix core implementation",
    "body": "The core file needs an implementation fix.",
    "repository_name": "agentic-github-employee"
  }'
```

The response is an `AgenticState` containing the generated plan, proposed file
changes, review feedback, run status, revision count, and execution trace.

## Quality Checks

```bash
uv run ruff check src
uv run mypy src
uv run pytest
```

## Docker

`docker-compose.yml` is present for the planned backend container and PostgreSQL
telemetry database. The current supported MVP run path is local execution with
UV:

```bash
uv run uvicorn src.interface.main:app --reload
```

PostgreSQL is configured for future telemetry persistence. The current MVP uses
in-memory execution state and a mock sandbox runner. Docker execution should be
enabled after `docker/app.Dockerfile` is completed.
