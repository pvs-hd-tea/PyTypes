from abc import ABC, abstractmethod
import pathlib

from .projio import Project
from .strat import ApplicationStrategy


class TestDetector(ABC):
    """
    When given the path to a repo, attempts to detect a specific
    testing suite and create the appropriate application strategy
    if there is a match.
    """

    def __init__(self, project: Project):
        # TODO: Should this take an instance of repository?
        # TODO: Perhaps a project class is needed, in order to interact better with the project structure
        self.project = project

    @abstractmethod
    def matches(self) -> bool:
        """Detect specific testing suite."""
        pass

    @abstractmethod
    def create_strategy(self) -> ApplicationStrategy:
        """Create application strategy."""
        pass


def detector_factory(proj: Project) -> TestDetector:
    pass
