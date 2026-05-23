from abc import ABC, abstractmethod

from src.domain.models import FileChange


SandboxResult = dict[str, bool | str]


class BaseSandboxRunner(ABC):
    @abstractmethod
    async def run_test_suite(self, changes: list[FileChange]) -> SandboxResult:
        """Run the project's test suite against proposed file changes."""
