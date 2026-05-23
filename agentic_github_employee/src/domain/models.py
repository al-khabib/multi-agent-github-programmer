from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AgentRole(StrEnum):
    PRODUCT_MANAGER = "PRODUCT_MANAGER"
    DEVELOPER = "DEVELOPER"
    REVIEWER = "REVIEWER"


class FileChange(BaseModel):
    model_config = ConfigDict(strict=True)

    file_path: str = Field(
        description="Repository-relative path of the file being changed."
    )
    code_diff: str = Field(
        description=(
            "Unified diff or patch content representing the proposed code change."
        )
    )
    justification: str = Field(
        description="Reasoning that explains why this file change is necessary."
    )


class GitHubIssue(BaseModel):
    model_config = ConfigDict(strict=True)

    issue_id: int = Field(description="Unique numeric identifier of the GitHub issue.")
    title: str = Field(description="Title of the GitHub issue.")
    body: str = Field(description="Body content of the GitHub issue.")
    repository_name: str = Field(
        description="Name of the repository that owns the GitHub issue."
    )


class ExecutionTrace(BaseModel):
    model_config = ConfigDict(strict=True)

    step_name: str = Field(
        description="Name of the orchestration step or agent action."
    )
    prompt_tokens: int = Field(
        description="Number of prompt tokens consumed by this execution step."
    )
    completion_tokens: int = Field(
        description="Number of completion tokens produced by this execution step."
    )
    latency_ms: float = Field(
        description="Observed latency of this execution step in milliseconds."
    )
    cost_usd: float = Field(
        description="Estimated model cost for this execution step in US dollars."
    )


class AgenticState(BaseModel):
    model_config = ConfigDict(strict=True)

    execution_id: UUID = Field(
        description="Unique identifier for this orchestrator execution."
    )
    issue: GitHubIssue = Field(
        description="GitHub issue being processed by the multi-agent system."
    )
    current_plan: str | None = Field(
        description="Current implementation plan produced by the product manager agent."
    )
    proposed_changes: list[FileChange] | None = Field(
        description="File changes proposed by the developer agent."
    )
    review_feedback: str | None = Field(
        description="Latest review feedback produced by the reviewer agent."
    )
    run_status: str = Field(
        description="Overall orchestration status for the multi-agent execution."
    )
    revision_count: int = Field(
        description="Number of implementation or review revision cycles completed."
    )
    history: list[ExecutionTrace] = Field(
        description="Chronological execution trace for orchestration observability."
    )
