from abc import ABC, abstractmethod
import pathlib

from .projio import Project


class ApplicationStrategy(ABC):
    """
    Implement for a specific test framework;
    When given a file that uses the specified framework,
    parse this file and insert code that will cause the test
    functions to be traced upon execution.
    """

    def apply(self, project: Project):
        assert project.test_directory is not None
        for path in filter(self._test_file_filter, project.test_directory.glob("**/*")):
            self._apply(path)

    @abstractmethod
    def _apply(self, path: pathlib.Path) -> None:
        """Perform IO operation to modify the file pointed to by path"""
        pass

    @abstractmethod
    def _test_file_filter(self, path: pathlib.Path) -> bool:
        """True iff path is a file / folder that will be executed by the framework"""
        pass


class PyTestStrategy(ApplicationStrategy):
    def _apply(self, path: pathlib.Path) -> None:
        pass

    def _test_file_filter(self, path: pathlib.Path) -> bool:
        pass
