from operator import add
from time import perf_counter
from typing import Annotated, Literal, TypedDict, cast
from uuid import UUID

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.domain.models import AgenticState, ExecutionTrace, FileChange, GitHubIssue
from src.infrastructure.interfaces import BaseSandboxRunner

INPUT_TOKEN_COST_PER_1K = 0.0015
OUTPUT_TOKEN_COST_PER_1K = 0.006
MAX_REVISION_COUNT = 5

RouteDecision = Literal["developer_node", "__end__"]
RunStatus = Literal["RUNNING", "REVISING", "SUCCEEDED", "FAILED"]


class AgenticGraphState(TypedDict):
    execution_id: UUID
    issue: GitHubIssue
    current_plan: str | None
    proposed_changes: Annotated[list[FileChange], add]
    review_feedback: str | None
    run_status: RunStatus
    revision_count: int
    history: Annotated[list[ExecutionTrace], add]


class AgenticGraphUpdate(TypedDict, total=False):
    current_plan: str
    proposed_changes: list[FileChange]
    review_feedback: str
    run_status: RunStatus
    revision_count: int
    history: list[ExecutionTrace]


class LangGraphOrchestrator:
    def __init__(self, sandbox_runner: BaseSandboxRunner) -> None:
        self._sandbox_runner = sandbox_runner
        self.graph = self._build_graph()

    def _build_graph(
        self,
    ) -> CompiledStateGraph[
        AgenticGraphState, None, AgenticGraphState, AgenticGraphState
    ]:
        workflow = StateGraph(AgenticGraphState)

        workflow.add_node("product_manager_node", self.product_manager_node)
        workflow.add_node("developer_node", self.developer_node)
        workflow.add_node("reviewer_node", self.reviewer_node)

        workflow.set_entry_point("product_manager_node")
        workflow.add_edge("product_manager_node", "developer_node")
        workflow.add_edge("developer_node", "reviewer_node")
        workflow.add_conditional_edges("reviewer_node", self._route_after_review)

        return workflow.compile()

    async def run(self, initial_state: AgenticState) -> AgenticState:
        graph_input = self._to_graph_state(initial_state)
        graph_output = await self.graph.ainvoke(graph_input)
        return self._to_domain_state(cast(AgenticGraphState, graph_output))

    async def product_manager_node(
        self, state: AgenticGraphState
    ) -> AgenticGraphUpdate:
        return {
            "current_plan": "Fix implementation in core file.",
            "run_status": "RUNNING",
            "history": [self._build_trace("product_manager_node", 0.0)],
        }

    async def developer_node(self, state: AgenticGraphState) -> AgenticGraphUpdate:
        return {
            "proposed_changes": [
                FileChange(
                    file_path="src/core.py",
                    code_diff=(
                        "--- a/src/core.py\n"
                        "+++ b/src/core.py\n"
                        "@@ -1,2 +1,2 @@\n"
                        "-pass\n"
                        "+return True\n"
                    ),
                    justification=(
                        "Apply the current implementation plan to the core file."
                    ),
                )
            ],
            "history": [self._build_trace("developer_node", 0.0)],
        }

    async def reviewer_node(self, state: AgenticGraphState) -> AgenticGraphUpdate:
        started_at = perf_counter()
        sandbox_result = await self._sandbox_runner.run_test_suite(
            state["proposed_changes"]
        )
        latency_ms = (perf_counter() - started_at) * 1000

        if sandbox_result["success"] is True:
            return {
                "review_feedback": "APPROVED",
                "run_status": "SUCCEEDED",
                "history": [self._build_trace("reviewer_node", latency_ms)],
            }

        next_revision_count = state["revision_count"] + 1
        run_status: RunStatus = (
            "FAILED"
            if next_revision_count >= MAX_REVISION_COUNT
            else "REVISING"
        )
        review_feedback = (
            "FAILED_MAX_REVISIONS"
            if next_revision_count >= MAX_REVISION_COUNT
            else "REJECTED"
        )

        return {
            "review_feedback": review_feedback,
            "run_status": run_status,
            "revision_count": next_revision_count,
            "history": [self._build_trace("reviewer_node", latency_ms)],
        }

    def _route_after_review(self, state: AgenticGraphState) -> RouteDecision:
        if state["review_feedback"] == "APPROVED":
            return cast(RouteDecision, END)

        if state["revision_count"] >= MAX_REVISION_COUNT:
            return cast(RouteDecision, END)

        return "developer_node"

    def _build_trace(self, step_name: str, latency_ms: float) -> ExecutionTrace:
        prompt_tokens, completion_tokens = self._simulated_token_usage(step_name)
        cost_usd = self._calculate_cost_usd(prompt_tokens, completion_tokens)

        return ExecutionTrace(
            step_name=step_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
        )

    def _simulated_token_usage(self, step_name: str) -> tuple[int, int]:
        token_usage: dict[str, tuple[int, int]] = {
            "product_manager_node": (1200, 400),
            "developer_node": (2500, 800),
            "reviewer_node": (1800, 300),
        }
        return token_usage[step_name]

    def _calculate_cost_usd(
        self, prompt_tokens: int, completion_tokens: int
    ) -> float:
        input_cost = (prompt_tokens / 1000) * INPUT_TOKEN_COST_PER_1K
        output_cost = (completion_tokens / 1000) * OUTPUT_TOKEN_COST_PER_1K
        return round(input_cost + output_cost, 6)

    def _to_graph_state(self, state: AgenticState) -> AgenticGraphState:
        return {
            "execution_id": state.execution_id,
            "issue": state.issue,
            "current_plan": state.current_plan,
            "proposed_changes": state.proposed_changes or [],
            "review_feedback": state.review_feedback,
            "run_status": self._coerce_run_status(state.run_status),
            "revision_count": state.revision_count,
            "history": state.history,
        }

    def _to_domain_state(self, state: AgenticGraphState) -> AgenticState:
        return AgenticState(
            execution_id=state["execution_id"],
            issue=state["issue"],
            current_plan=state["current_plan"],
            proposed_changes=state["proposed_changes"],
            review_feedback=state["review_feedback"],
            run_status=state["run_status"],
            revision_count=state["revision_count"],
            history=state["history"],
        )

    def _coerce_run_status(self, run_status: str) -> RunStatus:
        if run_status in {"RUNNING", "REVISING", "SUCCEEDED", "FAILED"}:
            return cast(RunStatus, run_status)

        return "RUNNING"
