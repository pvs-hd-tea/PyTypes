from abc import ABC, abstractmethod
import pathlib
import typing

from .projio import Project


class ApplicationStrategy(ABC):
    """
    Implement for a specific test framework;
    When given a file that uses the specified framework,
    parse this file and insert code that will cause the test
    functions to be traced upon execution.
    """

    def apply(self, project: Project):
        for match in self.test_file_filter():
            self._apply(match)

    @abstractmethod
    def _apply(self, test_file: pathlib.Path) -> None:
        pass

    @abstractmethod
    def test_file_filter(self) -> typing.Iterator[pathlib.Path]:
        pass

class PyTestStrategy(ApplicationStrategy):
    def apply(self, project: Project):
        pass
