from abc import abstractmethod
import pathlib


class ApplicationStrategy:
    pass


class TestDetector:
    """
    When given the path to a repo, attempts to detect a specific
    testing suite and create the appropriate application strategy
    if there is a match.
    """

    def __init__(self, path2project: pathlib.Path):
        # TODO: Should this take an instance of repository?
        self.path2project = path2project

    @abstractmethod
    def matches(self) -> bool:
        """Detect specific testing suite."""
        pass

    @abstractmethod
    def create_strategy(self) -> ApplicationStrategy:
        """Create application strategy."""
        pass
