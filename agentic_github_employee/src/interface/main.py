from uuid import uuid4

import uvicorn
from fastapi import FastAPI

from src.application.orchestrator import LangGraphOrchestrator
from src.domain.models import AgenticState, GitHubIssue
from src.infrastructure.mock_sandbox import MockSandboxRunner

app = FastAPI(title="The Agentic GitHub Employee")


@app.post("/webhook/issue", response_model=AgenticState)
async def handle_issue_webhook(issue: GitHubIssue) -> AgenticState:
    sandbox_runner = MockSandboxRunner()
    orchestrator = LangGraphOrchestrator(sandbox_runner)
    initial_state = AgenticState(
        execution_id=uuid4(),
        issue=issue,
        current_plan=None,
        proposed_changes=None,
        review_feedback=None,
        run_status="RUNNING",
        revision_count=0,
        history=[],
    )

    return await orchestrator.run(initial_state)


if __name__ == "__main__":
    uvicorn.run("src.interface.main:app", host="0.0.0.0", port=8000, reload=True)
