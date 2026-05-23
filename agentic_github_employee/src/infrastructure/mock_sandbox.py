from src.domain.models import FileChange
from src.infrastructure.interfaces import BaseSandboxRunner, SandboxResult


class MockSandboxRunner(BaseSandboxRunner):
    async def run_test_suite(self, changes: list[FileChange]) -> SandboxResult:
        has_syntax_error = any("syntax_error" in change.code_diff for change in changes)

        if has_syntax_error:
            return {"success": False, "output": "SyntaxError: invalid syntax"}

        return {"success": True, "output": "All 12 tests passed successfully."}
