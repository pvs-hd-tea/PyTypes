from abc import ABC, abstractmethod
import pathlib
import logging

import toml

from .projio import Project
from .strat import ApplicationStrategy, PyTestStrategy


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


class PyTestDetector(TestDetector):
    def __init__(self, project: Project):
        super().__init__(project)

    def matches(self) -> bool:
        return self._has_pytest_ini() or self._has_pytest_in_pyproject()

    def create_strategy(self) -> ApplicationStrategy:
        return PyTestStrategy()

    def _has_pytest_ini(self) -> bool:
        pytest_config = self.project.root / "pytest.ini"
        return pytest_config.is_file()

    def _has_pytest_in_pyproject(self) -> bool:
        pyproj = self.project.root / "pyproject.toml"
        if not pyproj.is_file():
            return False

        pyproj_cfg = toml.load(pyproj.open())
        return (
            "tool" in pyproj_cfg
            and "poetry" in pyproj_cfg["tool"]
            and "dev-dependencies" in pyproj_cfg["tool"]["poetry"]
            and "pytest" in pyproj_cfg["tool"]["poetry"]["dev-dependencies"]
        )


def detector_factory(proj: Project) -> TestDetector:
    if (d := PyTestDetector(proj)).matches():
        logging.info(f"Detected pytest in {proj.root}")
        return d

    raise LookupError(f"Project at {proj.root} uses unknown testing suite")
