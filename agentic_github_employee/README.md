## High Level Agent Architecture
```
[ GitHub Webhook ]
               │
               ▼
       1. Triage Agent (Assigns & Plans)
               │
               ▼
       2. Coder Agent (Writes Fix) ◄──────┐
               │                          │
               ▼                          │ (If Changes Requested)
       3. Reviewer Agent (Tests & Lints) ─┘
               │
               ▼
       4. Gatekeeper Agent (HITL Approval) ──► [ Merge to Main ]

```

## Start FastAPI backend

```
uv run uvicoen main:app --reload
```

## Run linters and type checkers
```
uv run ruff check
uv run mypy .

```
