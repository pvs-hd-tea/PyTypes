from abc import ABC, abstractmethod
import pathlib


class ApplicationStrategy(ABC):
    pass


class TestDetector(ABC):
    """
    When given the path to a repo, attempts to detect a specific
    testing suite and create the appropriate application strategy
    if there is a match.
    """

    def __init__(self, path2project: pathlib.Path):
        # TODO: Should this take an instance of repository?
        # TODO: Perhaps a project class is needed, in order to interact better with the project structure
        self.path2project = path2project

    @abstractmethod
    def matches(self) -> bool:
        """Detect specific testing suite."""
        pass

    @abstractmethod
    def create_strategy(self) -> ApplicationStrategy:
        """Create application strategy."""
        pass
