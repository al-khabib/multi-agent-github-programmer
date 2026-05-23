from typing import Literal

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.domain.models import AgenticState, FileChange
from src.infrastructure.interfaces import BaseSandboxRunner

RouteDecision = Literal["developer_node", "__end__"]


class LangGraphOrchestrator:
    def __init__(self, sandbox_runner: BaseSandboxRunner) -> None:
        self._sandbox_runner = sandbox_runner
        self.graph = self._build_graph()

    def _build_graph(
        self,
    ) -> CompiledStateGraph[AgenticState, None, AgenticState, AgenticState]:
        workflow = StateGraph(AgenticState)

        workflow.add_node("product_manager_node", self.product_manager_node)
        workflow.add_node("developer_node", self.developer_node)
        workflow.add_node("reviewer_node", self.reviewer_node)

        workflow.set_entry_point("product_manager_node")
        workflow.add_edge("product_manager_node", "developer_node")
        workflow.add_edge("developer_node", "reviewer_node")
        workflow.add_conditional_edges("reviewer_node", self._route_after_review)

        return workflow.compile()

    async def run(self, initial_state: AgenticState) -> AgenticState:
        final_state = await self.graph.ainvoke(initial_state)
        return AgenticState.model_validate(final_state)

    async def product_manager_node(self, state: AgenticState) -> AgenticState:
        return state.model_copy(
            update={"current_plan": "Fix implementation in core file."}
        )

    async def developer_node(self, state: AgenticState) -> AgenticState:
        proposed_changes = list(state.proposed_changes or [])
        proposed_changes.append(
            FileChange(
                file_path="src/core.py",
                code_diff=(
                    "--- a/src/core.py\n"
                    "+++ b/src/core.py\n"
                    "@@ -1,2 +1,2 @@\n"
                    "-pass\n"
                    "+return True\n"
                ),
                justification="Apply the current implementation plan to the core file.",
            )
        )

        return state.model_copy(update={"proposed_changes": proposed_changes})

    async def reviewer_node(self, state: AgenticState) -> AgenticState:
        proposed_changes = state.proposed_changes or []
        sandbox_result = await self._sandbox_runner.run_test_suite(proposed_changes)

        if sandbox_result["success"] is True:
            return state.model_copy(update={"review_feedback": "APPROVED"})

        return state.model_copy(
            update={
                "review_feedback": "REJECTED",
                "revision_count": state.revision_count + 1,
            }
        )

    def _route_after_review(self, state: AgenticState) -> RouteDecision:
        if state.review_feedback == "APPROVED":
            return END

        return "developer_node"
